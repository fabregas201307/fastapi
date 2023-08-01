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
import numpy as np
import pandas as pd
import tqdm
import warnings
warnings.filterwarnings('ignore')


class StockCNN(nn.Module):
    def __init__(self):
        super(StockCNN, self).__init__()

        # First layer
        kernel_size = (5, 3)
        stride = (3, 1)
        dilation = (2, 1)
        padding1 = ((stride[0]*(96-1) + dilation[0]*(kernel_size[0]-1) - 96 + 2)//2,
                   (stride[1]*(180-1) + dilation[1]*(kernel_size[1]-1) - 180 + 2)//2)

        self.conv1 = nn.Conv2d(in_channels=1, out_channels=64, kernel_size=kernel_size,
                                stride=stride, padding=padding1, dilation=dilation)
        init.xavier_uniform_(self.conv1.weight)
        init.zeros_(self.conv1.bias)

        self.maxpool1 = nn.MaxPool2d(kernel_size=(2, 1))
        self.batch_norm1 = nn.BatchNorm2d(64)
        self.leaky_relu1 = nn.LeakyReLU()

        # Second layer
        padding2 = ((strid[0]*(48-1) + dilation[0]*(kernel_size[0]-1) - 48 + 2)//2,
                    (stride[1]*(180-1) + dilation[1]*(kernel_size[1]-1) - 180 + 2)//2)

        self.conv2 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=kernel_size,
                                stride=stride, padding=padding2, dilation=dilation)
        init.xavier_uniform_(self.conv2.weight)
        init.zeros_(self.conv2.bias)

        self.maxpool2 = nn.MaxPool2d(kernel_size=(2, 1))
        self.batch_norm2 = nn.BatchNorm2d(128)
        self.leaky_relu2 = nn.LeakyReLU()

        # Third layer
        padding3 = ((strid[0]*(24-1) + dilation[0]*(kernel_size[0]-1) - 24 + 2)//2,
                    (stride[1]*(90-1) + dilation[1]*(kernel_size[1]-1) - 90 + 2)//2)

        self.conv3 = nn.Conv2d(in_channels=128, out_channels=256, kernel_size=kernel_size,
                               stride=stride, padding=padding3, dilation=dilation)
        init.xavier_uniform_(self.conv3.weight)
        init.zeros_(self.conv3.bias)

        self.maxpool3 = nn.MaxPool2d(kernel_size=(2, 1))
        self.batch_norm3 = nn.BatchNorm2d(256)
        self.leaky_relu3 = nn.LeakyReLU()

        # Fourth layer
        padding4 = ((strid[0]*(12-1) + dilation[0]*(kernel_size[0]-1) - 12 + 2)//2,
                    (stride[1]*(45-1) + dilation[1]*(kernel_size[1]-1) - 45 + 2)//2)

        self.conv4 = nn.Conv2d(in_channels=256, out_channels=512, kernel_size=kernel_size,
                               stride=stride, padding=padding4, dilation=dilation)
        init.xavier_uniform_(self.conv4.weight)
        init.zeros_(self.conv4.bias)

        self.maxpool4 = nn.MaxPool2d(kernel_size=(2, 1))
        self.batch_norm4 = nn.BatchNorm2d(512)
        self.leaky_relu4 = nn.LeakyReLU()

        self.dropout = nn.Dropout(0.5)
        self.fc = nn.Linear(552960, 1)
        init.xavier_uniform_(self.fc.weight)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.conv1(x)
        x = self.maxpool1(x)
        x = self.batch_norm1(x)
        x = self.leaky_relu1(x)

        x = self.conv2(x)
        x = self.maxpool2(x)
        x = self.batch_norm2(x)
        x = self.leaky_relu2(x)

        x = self.conv3(x)
        x = self.maxpool3(x)
        x = self.batch_norm3(x)
        x = self.leaky_relu3(x)

        x = self.conv4(x)
        x = self.maxpool4(x)
        x = self.batch_norm4(x)
        x = self.leaky_relu4(x)

        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        x = self.fc(x)
        # x = self.sigmoid(x)
        return x


if __name__ == '__main__':
    my_path = '/fiquant/fiquant_prod/abalpha-jupyter/kai_wen/cnn_information/deeplake'
    ds = deeplake.load(my_path)
    ds = deeplake.load('/export/opt/tensor/cnn_ta/data/shallowlake')
    BATCH_SIZE=32
    MODES_PATH = "/fiquant/fiquant_prod/abalpha-jupyter/kai_wen/cnn_information/"

    device = 'cpu'
    net = torch.load(MODES_PATH + model, map_location=torch.device('cpu'))
    data_loader = ds.pytorch(batch_size=BATCH_SIZE, shuffle=False, num_workers=4)

    for model in ['model_2.pt']:
        print(f"Getting preds for {model}")
        # net = torch.load(MODES_PATH + model)
        net = torch.load(MODES_PATH + model, map_location=torch.device('cpu'))
        net.eval()
        pred_list = []
        with torch.no_grad():
            ###
            for i, data in enumerate(tqdm(data)):
                try:
                    images, labels = data['images'].to(device), data['labels'].to(device)
                    images = images.reshape(-1, 1, 96, 180)
                    predictions = np.array(net(images.float()).to('cpu')).flatten()
                    cusips, dates = data['cusip'], data['date']
                    # print(dates)
                    preds = pd.DataFrame(np.array([dates, cusips, predictions]))
                    # print(preds)
                    pred_list.append(preds)
                except RuntimeError:
                    print(f"Testing failed at batch")
        all_predictions = pd.concat([x.T for x in pred_list])
        all_predictions.columns = ['date', 'identifier', 'pred']
        all_predictions['date'] = pd.to_datetime(all_predictions['date'])
        all_predictions['pred'] = all_predictions['pred'].astype('float')
        all_predictions = all_predictions.drop_duplicates(['date', 'identifier'])
        all_predictions = all_predictions.pivot(index='date', columns='identifier', values='pred').sort_index()
        all_predictions = all_predictions.ffill(limit=22).asfreq('BM')
        all_predictions.index = [x for x in all_predictions.index]
        all_predictions.to_parquet(f"/fiquant/fiquant_prod/abalpha-jupyter/kai_wen/cnn_information/cnn_preds_{model.split('.')[0]}.parquet")

    # model = "model_2.pt"
    # device = 'cpu'
    # net = torch.load(MODES_PATH + model, map_location=torch.device('cpu'))

    # data_loader = ds.pytorch(batch_size=BATCH_SIZE, shuffle=False, num_workers=4)

    # images, labels = data['images'].to(device), data['labels'].to(device)
    # images = images.reshape(-1, 1, 96, 180)
    # predictions = np.array(net(images.float()).to('cpu')).flatten()
