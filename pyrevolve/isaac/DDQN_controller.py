import random

import torch
import torch.optim as optim
import numpy as np
from collections import deque

import torch
from torch import nn
from torch.autograd.grad_mode import F

class NeuralNetwork(torch.nn.Module):

    def __init__(self, n_input, n_hidden, n_output):
        super(NeuralNetwork, self).__init__()
        self.online = nn.Sequential(
            nn.Linear(n_input, n_hidden),
            nn.ReLU(),
            # nn.Linear(n_hidden, n_hidden),
            # nn.ReLU(),
            # nn.ReLU(),
            nn.Linear(n_hidden, n_output)
        )
        self.target = copy.deepcopy(self.online)

        # Q_target parameters are frozen.
        for p in self.target.parameters():
            p.requires_grad = False

    def forward(self, state, model):
        if model == "online":
            return self.online(state)
        elif model == "target":
            return self.target(state)

class ReinforcementLearningAgent:
    """Reinforcement learner class with experience replay. Initialized by specifiable NN mapping. """

    def __init__(self, n_state, n_action):
        self.curr_step = 0
        self.training_size = 1000
        self.n_state = n_state
        self.n_action = n_action

        self.memory = deque(maxlen=2000)
        self.batch_size = 32

        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.001

        self.model = NeuralNetwork(n_state, n_state, n_action)

        self.learn = 0.1
        self.beta1 = 0.9
        self.beta2 = 0.999
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learn, betas=(self.beta1, self.beta2))
        self.loss_fn = torch.nn.MSELoss()

    def td_estimate(self, state, action):
        current_Q = self.model(state, model="online")[
            np.arange(0, self.batch_size), action
        ]  # Q_online(s,a)
        return current_Q

    @torch.no_grad()
    def td_target(self, reward, next_state, done):
        next_state_Q = self.model(next_state, model="online")
        best_action = torch.argmax(next_state_Q, axis=1)
        next_Q = self.model(next_state, model="target")[
            np.arange(0, self.batch_size), best_action
        ]
        return (reward + (1 - done.float()) * self.gamma * next_Q).float()

    def update_Q_online(self, td_estimate, td_target):
        loss = self.loss_fn(td_estimate, td_target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def sync_Q_target(self):
        self.model.target.load_state_dict(self.model.online.state_dict())
        # print("first batch learned")

    def step(self, state):
        """
    Given a state, choose an epsilon-greedy action and update value of step.

    Inputs:
    <np.array> state : A single observation of the current state, dimension is (state_dim)
    Outputs:
    <int> action_idx: An integer representing which action Mario will perform
    """
        # EXPLORE
        if np.random.rand() < self.epsilon:
            action_idx = np.random.randint(self.n_action)
        # EXPLOIT
        else:
            state = state.__array__()
            state = torch.tensor(state)
            state = state.unsqueeze(0).double()
            action_values = self.model(state.float(), model="online")
            action_idx = torch.argmax(action_values).item()
        # increment step
        self.curr_step += 1
        return action_idx

    def remember(self, state, action, reward, next_state, done):
        state = torch.tensor(state, dtype=torch.float)
        action = torch.tensor([action])
        reward = torch.tensor([reward])
        next_state = torch.tensor(next_state, dtype=torch.float)
        done = torch.tensor([done])
        self.memory.append((state, action, reward, next_state, done))
        if len(self.memory) > self.training_size:
            self.decay_epsilon()

    def decay_epsilon(self):
        if self.epsilon <= self.epsilon_min:
            return
        self.epsilon *= (1 - self.epsilon_decay)

    def replay(self):
        if len(self.memory) < 5 * self.batch_size:
            return
        # Randomly sample minibatch from the memory
        minibatch = random.sample(self.memory, min(len(self.memory), self.batch_size))
        state, action, reward, next_state, done = map(torch.stack, zip(*minibatch))
        state = state.squeeze()
        action = action.squeeze()
        reward = reward.squeeze()
        next_state = next_state.squeeze()
        done = done.squeeze()

        if self.curr_step % 5 == 0:
            self.sync_Q_target()

        # Get TD Estimate
        td_est = self.td_estimate(state, action)
        # Get TD Target
        td_tgt = self.td_target(reward, next_state, done)
        # Backpropagate loss through Q_online
        self.update_Q_online(td_est, td_tgt)