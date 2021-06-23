#%%
import numpy as np
import torch
from torch import nn
import torch.optim as optim
import scipy.integrate as integrate
import matplotlib.pyplot as plt

class NeuralNetwork(torch.nn.Module):

    def __init__(self, n_input, n_hidden, n_output):
        super(NeuralNetwork, self).__init__()
        self.NN = nn.Sequential(
            nn.Linear(n_input, n_hidden),
            nn.ReLU(),
            nn.ReLU(),
            nn.Linear(n_hidden, n_output),
            nn.Tanh()
        )

    def forward(self, state):
        return self.NN(state)


class DC():
    def __init__(self, n_state, n_action):
        self.n_state = n_state
        self.n_action = n_action
        self.model = NeuralNetwork(n_state*2+n_action, n_state, n_state)

        self.learn = 0.1
        self.beta1 = 0.9
        self.beta2 = 0.999
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learn, betas=(self.beta1, self.beta2))
        self.loss_fn = torch.nn.MSELoss()

    def dc_cost_func (self, X_opt):
        t_f = X_opt[-1]
        return t_f

    def dc_cost_grad_func (self, X_opt):
        grad = np.zeros(len(X_opt))
        grad[-1] = 1.0 #X_opt[0] #
        return grad

    def dc_cons_func(self, X_opt):
        """DC_function set up equality constraints at every collocation point.
           These constraints induce discrete differences to conform to the EOM.
           Lastly, initial- and end-states can be imposed as wel"""
        n = int(len(X_opt)/(self.n_state + self.n_action))
        x = torch.tensor(X_opt[1:].reshape((n, self.n_state + self.n_action))).type(torch.float)
        t = np.linspace(0, 30, n)
        dt = t[1] - t[0]

        # Collocation points
        xdot = self.model.forward(x)
        xll = x[:-1, :-self.n_action]
        xrr = x[1:, :-self.n_action]
        xdotll = xdot[:-1, :]
        xdotrr = xdot[1:, :]
        ull = x[:-1, -self.n_action:]
        urr = x[1:, -self.n_action:]

        xc = .5 * (xll + xrr) + dt / 8 * (xdotll - xdotrr)
        uc = (ull + urr) / 2
        dc = torch.cat((xc, uc), 1)
        xdotc = self.model.forward(dc)

        # Equality Constraints
        Ceq = (xll - xrr) + dt / 6 * (xdotll + 4 * xdotc + xdotrr)
        Ceq = Ceq.reshape(np.prod(Ceq.shape))
        Ceq = torch.cat((Ceq, x[0, :2] - torch.tensor([10,0]).type(torch.float)), 0)
        Ceq = torch.cat((Ceq, x[-1,:2] - torch.tensor([0,0]).type(torch.float)), 0).detach()
        return Ceq.numpy()

    def update_model(self, stated_pred, stated_real):
        loss = self.loss_fn(stated_pred, stated_real)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

