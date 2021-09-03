from typing import Callable, List, Tuple

import numpy as np
import scipy.stats as stats
from sklearn.neighbors import KNeighborsRegressor

# call `step` repeatedly to get 'better' weights


class RevDEknn:
    def __init__(
        self,
        calculate_fitnesses: Callable[[List[float]], float],
        gamma: float,
        clip_min: float,
        clip_max: float,
        cr,  # float or array like of floats?
        seedhack: int,
    ):
        self.calculate_fitnesses = calculate_fitnesses
        self.gamma = gamma
        self.clip_min = clip_min
        self.clip_max = clip_max
        self.cr = cr

        R = np.asarray(
            [
                [1, self.gamma, -self.gamma],
                [
                    -self.gamma,
                    1.0 - self.gamma ** 2,
                    self.gamma + self.gamma ** 2,
                ],
                [
                    self.gamma + self.gamma ** 2,
                    -self.gamma + self.gamma ** 2 + self.gamma ** 3,
                    1.0 - 2.0 * self.gamma ** 2 - self.gamma ** 3,
                ],
            ]
        )

        self.R = np.expand_dims(R, 0)  # 1 x 3 x 3

        self.nn = KNeighborsRegressor(n_neighbors=3)

        self.X: np.ndarray = None  # numpy.ndarray 2D with each column indices/weights
        self.E: np.ndarray = None  # numpy.ndarray 1D of fitness values corresponding to each list of indices

        self.seedhack = seedhack
        self.seedi = 0

    def _proposal(self, theta: np.ndarray, E=None):

        if self.X is None:
            self.X = theta
            self.E = E
        else:
            if self.X.shape[0] < 10000:
                self.X = np.concatenate((self.X, theta), 0)
                self.E = np.concatenate((self.E, E), 0)

        self.nn.fit(self.X, self.E)

        theta_0 = np.expand_dims(theta, 1)  # B x 1 x D

        # :(
        np.random.seed(self.seedhack + self.seedi % 1000000)
        self.seedi += 1

        indices_1 = np.random.permutation(theta.shape[0])
        indices_2 = np.random.permutation(theta.shape[0])
        theta_1 = np.expand_dims(theta[indices_1], 1)
        theta_2 = np.expand_dims(theta[indices_2], 1)

        tht = np.concatenate((theta_0, theta_1, theta_2), 1)  # B x 3 x D

        y = np.matmul(self.R, tht)

        theta_new = np.concatenate((y[:, 0], y[:, 1], y[:, 2]), 0)

        p_1 = np.random.binomial(1, self.cr, theta_new.shape)
        theta_new = p_1 * theta_new + (1.0 - p_1) * np.concatenate(
            (tht[:, 0], tht[:, 1], tht[:, 2]), 0
        )

        E_pred = self.nn.predict((theta_new))

        ind = np.argsort(E_pred.squeeze())

        return theta_new[ind[: theta.shape[0]]]

    async def step(self, theta, E_old) -> Tuple[np.ndarray, float]:
        """
        theta: numpy.ndarray 2D with first dimension population size, second dimension # weights
               this is what we are optimizing
        E_old: numpy.ndarray 1D with each item a fitness value for the individual at the same index in the population
        """

        # (1. Generate)
        theta_new = self._proposal(theta, E_old)
        theta_new = np.clip(
            theta_new,
            a_min=self.clip_min,
            a_max=self.clip_max,
        )

        # (2. Evaluate)
        E_new = await self.calculate_fitnesses(
            theta_new,
        )

        # (3. Select)
        theta_cat = np.concatenate((theta, theta_new), 0)
        E_cat = np.concatenate((E_old, E_new), 0)

        indx = np.argsort(E_cat.squeeze())

        return theta_cat[indx[: theta.shape[0]], :], E_cat[indx[: theta.shape[0]], :]
