import numpy as np


def RK45(state, A, dt):
    A1 = np.matmul(A, state)
    A2 = np.matmul(A, (state + dt / 2 * A1))
    A3 = np.matmul(A, (state + dt / 2 * A2))
    A4 = np.matmul(A, (state + dt * A3))
    return state + dt / 6 * (A1 + 2 * (A2 + A3) + A4)


class CPG():
    def __init__(self, weights, dt):
        self.dt = dt
        self.state_shape = (len(weights) * 2, int(1))
        weights = np.insert(weights, range(1, len(weights)), 0)
        wx_wy = np.diag(weights, 1)
        wy_wx = np.diag(-weights, -1)
        self.A = wx_wy + wy_wx
        self.y = np.ones(self.state_shape) * np.sqrt(2) / 2

    def update_CPG(self):
        y_t = RK45(self.y[:, -1], self.A, self.dt).reshape(self.state_shape)
        self.y = np.hstack((self.y, y_t))
        return np.array(y_t[::2])

    def reset_controller(self):
        y_t = np.ones(self.state_shape) * np.sqrt(2) / 2
        self.y = np.hstack((self.y, y_t))
        # return np.array(y_t[::2])

    def set_weights(self, weights):
        weights = np.insert(weights, range(1, len(weights)), 0)
        wx_wy = np.diag(weights, 1)
        wy_wx = np.diag(-weights, -1)
        self.A = wx_wy + wy_wx
