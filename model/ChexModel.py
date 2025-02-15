from __future__ import print_function, division

# pytorch imports
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
from torch.autograd import Variable
import torchvision
from torchvision import datasets, models, transforms
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, utils

# image imports
from skimage import io, transform
from PIL import Image

# general imports
import os
import time
from shutil import copyfile
from shutil import rmtree

# data science imports
import pandas as pd
import numpy as np
import csv

import ChexDataset as CXR
import EvaluateModel as EM

use_gpu = torch.cuda.is_available()
gpu_count = torch.cuda.device_count()
print("Available GPU count:" + str(gpu_count))


def checkpoint(model, best_loss, epoch, LR):
    """
    Saves checkpoint of torchvision model during training.
    Code from https://pytorch.org/tutorials/beginner/saving_loading_models.html

    Args:
        model: torchvision model to be saved
        best_loss: best val loss achieved so far in training
        epoch: current epoch of training
        LR: current learning rate in training
    Returns:
        None
    """

    print('saving')
    # https: // pytorch.org / tutorials / beginner / saving_loading_models.html
    state = {
        'model': model,
        'best_loss': best_loss,
        'epoch': epoch,
        'rng_state': torch.get_rng_state(),
        'LR': LR
    }

    torch.save(state, 'results/checkpoint')


def train_model(
        model,
        criterion,
        optimizer,
        learning_rate,
        num_epochs,
        data_loaders,
        dataset_sizes,
        weight_decay):
    """
    Fine tunes torchvision model to NIH CXR data.

    Args:
        model: torchvision model to be finetuned (densenet-121)
        criterion: loss criterion (binary cross entropy loss, BCELoss)
        optimizer: optimizer to use in training (SGD)
        learning_rate: learning rate
        num_epochs: continue training up to this many epochs
        data_loaders: pytorch train and val dataloaders
        dataset_sizes: length of train and val datasets
        weight_decay: weight decay parameter we use in SGD with momentum
    Returns:
        model: trained torchvision model
        best_epoch: epoch on which best model val loss was obtained

    """
    since = time.time()

    start_epoch = 1
    best_loss = 999999
    best_epoch = -1
    last_train_loss = -1

    # This is mainly copy paste from homeworks except to adjust to accommodate for multiple dataloaders.
    # Other parts of code comes from collab notebooks we had experimented.
    # iterate over epochs
    for epoch in range(start_epoch, num_epochs + 1):
        print('Epoch {}/{}'.format(epoch, num_epochs))
        print('-' * 10)

        # set model to train or eval mode based on whether we are in train or
        # val; necessary to get correct predictions given batchnorm
        for phase in ['train', 'val']:
            print("Epoch {}/{}, phase:{}".format(epoch, num_epochs, phase))
            if phase == 'train':
                model.train(True)
            else:
                model.train(False)

            running_loss = 0.0

            i = 0
            total_done = 0
            #             print("Epoch {}/{}, phase:{}, start".format(epoch, num_epochs, phase))
            # iterate over all data in train/val dataloader:
            for data in data_loaders[phase]:
                #                 print("for:"+str(i))
                i += 1
                inputs, labels, _ = data
                #                 print("for-2:")
                batch_size = inputs.shape[0]
                #                 print("for-3:")
                labels = labels.float()
                #                 print("Epoch {}/{}, phase:{}, got input,labels".format(epoch, num_epochs, phase))
                if use_gpu:
                    inputs = Variable(inputs.cuda())
                    labels = Variable(labels.cuda()).float()

                #                 print("Epoch {}/{}, phase:{}, start-model(inputs)".format(epoch, num_epochs, phase))
                outputs = model(inputs)
                #                 print("Epoch {}/{}, phase:{}, end-model(inputs)".format(epoch, num_epochs, phase))

                # calculate gradient and update parameters in train phase
                #                 print("Epoch {}/{}, phase:{}, update grad".format(epoch, num_epochs, phase))
                optimizer.zero_grad()
                loss = criterion(outputs, labels)
                if phase == 'train':
                    loss.backward()
                    optimizer.step()
                #                 print("Epoch {}/{}, phase:{}, running_loss: {}".format(epoch, num_epochs, phase, running_loss))
                #                 current_loss =
                #                 if loss.data[0]
                running_loss += loss.item() * batch_size
                print("Epoch {}/{}, phase:{}, running_loss: {}, current_loss: {}".format(epoch, num_epochs, phase,
                                                                                         running_loss, loss.item()))

            epoch_loss = running_loss / dataset_sizes[phase]

            if phase == 'train':
                last_train_loss = epoch_loss

            print(phase + ' epoch {}:loss {:.4f} with data size {}'.format(
                epoch, epoch_loss, dataset_sizes[phase]))

            # decay learning rate if no val loss improvement in this epoch
            if phase == 'val' and epoch_loss > best_loss:
                print("decay loss from " + str(learning_rate) + " to " +
                      str(learning_rate / 10) + " as not seeing improvement in val loss")
                learning_rate = learning_rate / 10
                # create new optimizer with lower learning rate
                optimizer = optim.SGD(
                    filter(
                        lambda p: p.requires_grad,
                        model.parameters()),
                    lr=learning_rate,
                    momentum=0.9,
                    weight_decay=weight_decay)
                print("created new optimizer with LR " + str(learning_rate))

            # checkpoint model if has best val loss yet
            if phase == 'val' and epoch_loss < best_loss:
                best_loss = epoch_loss
                best_epoch = epoch
                checkpoint(model, best_loss, epoch, learning_rate)

            # log training and validation loss over each epoch
            if phase == 'val':
                with open("results/log_train", 'a') as logfile:
                    logw_riter = csv.writer(logfile, delimiter=',')
                    if (epoch == 1):
                        logw_riter.writerow(["epoch", "train_loss", "val_loss"])
                    logw_riter.writerow([epoch, last_train_loss, epoch_loss])

        total_done += batch_size
        if total_done % (100 * batch_size) == 0:
            print("completed " + str(total_done) + " so far in epoch")

        # break if no val loss improvement in 3 epochs
        if (epoch - best_epoch) >= 3:
            print("no improvement in 3 epochs, break")
            break

    time_elapsed = time.time() - since
    print('Training complete in {:.0f}m {:.0f}s'.format(
        time_elapsed // 60, time_elapsed % 60))

    # load best model weights to return
    checkpoint_best = torch.load('results/checkpoint')
    model = checkpoint_best['model']

    return model, best_epoch


def train_cnn(PATH_TO_IMAGES, PATH_TO_LABELS, learning_rate, WEIGHT_DECAY, use_gpu=False):
    """
    Train torchvision model to NIH data given high level hyperparameters.

    Args:
        PATH_TO_IMAGES: path to NIH images
        PATH_TO_LABELS: path to csv which contains labels
        learning_rate: learning rate
        WEIGHT_DECAY: weight decay parameter for SGD

    Returns:
        preds: torchvision model predictions on test fold with ground truth for comparison
        aucs: AUCs for each train,test tuple

    """
    NUM_EPOCHS = 100
    BATCH_SIZE = 16

    try:
        rmtree('results/')
    except BaseException:
        pass  # directory doesn't yet exist, no need to clear it
    os.makedirs("results/")

    # use imagenet mean,std for normalization
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]

    N_LABELS = 14  # we are predicting 14 labels

    # load labels
    # df = pd.read_csv("nih_labels.csv", index_col=0)

    # define torchvision transforms
    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomHorizontalFlip(),
            transforms.Scale(224),
            # because scale doesn't always give 224 x 224, this ensures 224 x
            # 224
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean, std)
        ]),
        'val': transforms.Compose([
            transforms.Scale(224),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean, std)
        ]),
    }

    # create train/val data_loaders
    transformed_datasets = {
        'train': CXR.ChexDataset(
            path_to_images=PATH_TO_IMAGES,
            path_to_labels_csv=PATH_TO_LABELS,
            fold='train',
            transform=data_transforms['train']),
        'val': CXR.ChexDataset(
            path_to_images=PATH_TO_IMAGES,
            path_to_labels_csv=PATH_TO_LABELS,
            fold='val',
            transform=data_transforms['val'])}

    data_loaders = {
        'train': torch.utils.data.DataLoader(
            transformed_datasets['train'],
            batch_size=BATCH_SIZE,
            shuffle=True,
            num_workers=8),
        'val': torch.utils.data.DataLoader(
            transformed_datasets['val'],
            batch_size=BATCH_SIZE,
            shuffle=True,
            num_workers=8)}

    # please do not attempt to train without GPU as will take excessively long
    # if not use_gpu:
    #     raise ValueError("Error, requires GPU")
    model = models.densenet121(pretrained=True)
    num_features = model.classifier.in_features
    # add final layer with # outputs in same dimension of labels with sigmoid
    # activation
    model.classifier = nn.Sequential(nn.Linear(num_features, N_LABELS), nn.Sigmoid())

    # put model on GPU
    if (use_gpu):
        is_gpu_available = torch.cuda.is_available()
        if not is_gpu_available:
            raise ValueError("Error, Can't use GPU since hardware doesn't Support it, you idiot!")
        gpu_count = torch.cuda.device_count()
        print("Using GPU: Available GPU count:" + str(gpu_count))

        model = model.cuda()

    # define criterion, optimizer for training
    criterion = nn.BCELoss()
    optimizer = optim.SGD(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=learning_rate,
        momentum=0.9,
        weight_decay=WEIGHT_DECAY)
    dataset_sizes = {x: len(transformed_datasets[x]) for x in ['train', 'val']}

    # train model
    model, best_epoch = train_model(model, criterion, optimizer, learning_rate, num_epochs=NUM_EPOCHS,
                                    data_loaders=data_loaders, dataset_sizes=dataset_sizes, weight_decay=WEIGHT_DECAY)

    # get preds and AUCs on test fold
    preds, aucs = EM.make_pred_multilabel(
        data_transforms, model, PATH_TO_IMAGES)

    return preds, aucs
