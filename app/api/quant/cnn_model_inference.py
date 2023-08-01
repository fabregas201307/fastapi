import os
import deeplake
import torch
from torch.nn import Module
from torch.nn import Conv2d
from torch.nn import Linear
from torch.nn import MaxPool2d
from torch.nn import LeakyReLU
from torch.nn.functional import softmax
from torch.optim import Adam
from torch.nn import CrossEntropyLoss
from torch import flatten
from torch import nn
# from Sophia import Sophia
from torch.nn import init