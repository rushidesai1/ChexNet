from __future__ import print_function, division

# pytorch imports
import torch
import torchvision
from torchvision import datasets, models, transforms
from torchvision import transforms, utils

# image / graphics imports
from skimage import io, transform
from PIL import Image
from pylab import *
import seaborn as sns
from matplotlib.pyplot import show

# data science
import numpy as np
import scipy as sp
import pandas as pd

# import other modules
from copy import deepcopy
import ChexDataset as CXR
import eval_model as E


def calc_cam(x, label, model):
    """
    function to generate a class activation map corresponding to a torch image tensor
    Args:
        x: the 1x3x224x224 pytorch tensor file that represents the NIH CXR
        label:user-supplied label you wish to get class activation map for; must be in labels list
        model: densenet121 trained on NIH CXR data
    Returns:
        cam_torch: 224x224 torch tensor containing activation map
    """
    labels = [
        'Atelectasis',
        'Cardiomegaly',
        'Effusion',
        'Infiltration',
        'Mass',
        'Nodule',
        'Pneumonia',
        'Pneumothorax',
        'Consolidation',
        'Edema',
        'Emphysema',
        'Fibrosis',
        'Pleural_Thickening',
        'Hernia']

    if label not in labels:
        raise ValueError(
            str(label) +
            "is an invalid label - please use one of " +
            str(labels))

    # find index for label; this corresponds to index from output of net
    label_index = next(
        (x for x in range(len(labels)) if labels[x] == label))

    # define densenet_last_layer class so we can get last 1024 x 7 x 7 output
    # of densenet for class activation map
    class densenet_last_layer(torch.nn.Module):
        def __init__(self, model):
            super(densenet_last_layer, self).__init__()
            self.features = torch.nn.Sequential(
                *list(model.children())[:-1]
            )

        def forward(self, x):
            x = self.features(x)
            x = torch.nn.functional.relu(x, inplace=True)
            return x

    # instantiate cam model and get output
    model_cam = densenet_last_layer(model)
    x = torch.autograd.Variable(x)
    y = model_cam(x)
    y = y.cpu().data.numpy()
    y = np.squeeze(y)

    # pull weights corresponding to the 1024 layers from model
    weights = model.state_dict()['classifier.0.weight']
    weights = weights.cpu().numpy()

    bias = model.state_dict()['classifier.0.bias']
    bias = bias.cpu().numpy()

    # can replicate bottleneck and probability calculation here from last_layer network and params from
    # original network to ensure that reconstruction is accurate -- commented out as previously checked

    # model_bn = deepcopy(model)
    # new_classifier = torch.nn.Sequential(*list(model_bn.classifier.children())[:-2])
    # model_bn.classifier = new_classifier
    # bn=model_bn(x)
    # recreate=0
    # bottleneck = []
    # for k in range(0,1024):
    #    avg_value = np.mean(y[k,:,:])# over the 7x7 grid
    #    bottleneck.append(avg_value)
    #    recreate = recreate+weights[label_index,k]*avg_value
    # recreate = recreate + bias[label_index]
    # recreate = 1/(1+math.exp(-recreate))
    # print("recalc:")
    # print(recreate)
    # print("original:")
    # print(model(x).data.numpy()[0][label_index])

    # create 7x7 cam
    cam = np.zeros((7, 7, 1))
    for i in range(0, 7):
        for j in range(0, 7):
            for k in range(0, 1024):
                cam[i, j] += y[k, i, j] * weights[label_index, k]
    cam += bias[label_index]

    # make cam into local region probabilities with sigmoid

    cam = 1 / (1 + np.exp(-cam))

    label_baseline_probs = {
        'Atelectasis': 0.103,
        'Cardiomegaly': 0.025,
        'Effusion': 0.119,
        'Infiltration': 0.177,
        'Mass': 0.051,
        'Nodule': 0.056,
        'Pneumonia': 0.012,
        'Pneumothorax': 0.047,
        'Consolidation': 0.042,
        'Edema': 0.021,
        'Emphysema': 0.022,
        'Fibrosis': 0.015,
        'Pleural_Thickening': 0.03,
        'Hernia': 0.002
    }

    # normalize by baseline probabilities
    cam = cam / label_baseline_probs[label]

    # take log
    cam = np.log(cam)

    return cam
