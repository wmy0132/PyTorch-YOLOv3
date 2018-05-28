from __future__ import division

from models import *
from utils.utils import *
from utils.datasets import *
from utils.parse_config import *

import os
import sys
import time
import datetime
import argparse

import torch
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision import transforms
from torch.autograd import Variable
import torch.optim as optim

parser = argparse.ArgumentParser()
parser.add_argument('--epochs', type=int, default=200, help='number of epochs')
parser.add_argument('--image_folder', type=str, default='data/samples', help='path to dataset')
parser.add_argument('--model_config_path', type=str, default='config/yolov3.cfg', help='path to model config file')
parser.add_argument('--data_config_path', type=str, default='config/coco.data', help='path to data config file')
parser.add_argument('--weights_path', type=str, default='weights/yolov3.weights', help='path to weights file')
parser.add_argument('--class_path', type=str, default='data/coco.names', help='path to class label file')
parser.add_argument('--conf_thres', type=float, default=0.8, help='object confidence threshold')
parser.add_argument('--nms_thres', type=float, default=0.4, help='iou thresshold for non-maximum suppression')
parser.add_argument('--n_cpu', type=int, default=0, help='number of cpu threads to use during batch generation')
parser.add_argument('--img_size', type=int, default=416, help='size of each image dimension')
parser.add_argument('--checkpoint_interval', type=int, default=10, help='interval between saving model weights')
parser.add_argument('--checkpoint_dir', type=str, default='checkpoints', help='directory where model checkpoints are saved')
opt = parser.parse_args()
print(opt)

os.makedirs('output', exist_ok=True)

cuda = True if torch.cuda.is_available else False

classes = load_classes(opt.class_path)

# Get data configuration
data_config     = parse_data_config(opt.data_config_path)
train_path      = data_config['train']

# Get hyper parameters
hyperparams     = parse_model_config(opt.model_config_path)[0]
batch_size      = int(hyperparams['batch'])
learning_rate   = float(hyperparams['learning_rate'])
momentum        = float(hyperparams['momentum'])
decay           = float(hyperparams['decay'])
burn_in         = int(hyperparams['burn_in'])

# Initiate model
model = Darknet(opt.model_config_path)
model.load_weights(opt.weights_path)

if cuda:
    model.cuda()

# Get dataloader
dataloader = torch.utils.data.DataLoader(
    ListDataset(train_path),
    batch_size=8, shuffle=False, num_workers=opt.n_cpu)

Tensor = torch.cuda.FloatTensor if cuda else torch.FloatTensor

optimizer = optim.SGD(model.parameters(), lr=learning_rate/batch_size, momentum=momentum, dampening=0, weight_decay=decay*batch_size)
for epoch in range(opt.epochs):
    for batch_i, (_, imgs, targets) in enumerate(dataloader):
        imgs = Variable(imgs.type(Tensor))
        targets = Variable(targets.type(Tensor), requires_grad=False)
        optimizer.zero_grad()

        loss = model(imgs, targets)

        loss.backward()
        optimizer.step()

    if epoch % opt.checkpoint_interval == 0:
        #model.save_weights('%s/%d.weights' % (opt.checkpoint_dir, epoch))
