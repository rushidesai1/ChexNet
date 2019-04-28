import pandas as pd
import numpy as np
from torch.utils.data import Dataset
import os
from PIL import Image


class ChexDataset(Dataset):

    def __init__(
            self,
            path_to_images,
            path_to_labels_csv,
            fold,
            transform=None,
            sample=0,
            label="any",
            sampled_images_path=None):

        # temporary, if we figure out way to do this during pre-processing we dont need this
        self.transform = transform
        self.path_to_images = path_to_images
        self.df = pd.read_csv(path_to_labels_csv)
        self.df = self.df[self.df['fold'] == fold]  # filter all images belonging to this fold

        if sampled_images_path is not None:
            sampled_images = pd.read_csv(sampled_images_path)
            # sampled_images shoulkd just contain image names deliminated by \n
            self.df = pd.merge(left=self.df, right=sampled_images, how="inner", on="Image Index")

        # can limit to sample, useful for testing
        # if fold == "train" or fold =="val": sample=500
        if 0 < sample < len(self.df):
            self.df = self.df.sample(sample)

        if not label == "any":  # can filter for positive findings of the kind described; useful for evaluation
            if label in self.df.columns:
                if len(self.df[self.df[label] == 1]) > 0:
                    self.df = self.df[self.df[label] == 1]
                else:
                    print("No positive cases exist for " + label + ", returning all unfiltered cases")
            else:
                print("cannot filter on label " + label +
                      " as not in data - please check spelling")

        self.df = self.df.set_index("Image Index")
        self.PRED_LABEL = [
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
        RESULT_PATH = "results/"

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):

        #         print("getItem: "+ str(idx)+"\n")

        # read custom format as defined in discussion with Fawy
        # convert to image format: mostly re-shape of array

        image = Image.open(
            os.path.join(
                self.path_to_images,
                self.df.index[idx]))
        image = image.convert('RGB')

        label = np.zeros(len(self.PRED_LABEL), dtype=int)
        for i in range(0, len(self.PRED_LABEL)):
            # can leave zero if zero, else make one
            if self.df[self.PRED_LABEL[i].strip()].iloc[idx].astype('int') > 0:
                label[i] = self.df[self.PRED_LABEL[i].strip()
                ].iloc[idx].astype('int')

        if self.transform:
            image = self.transform(image)

        return image, label, self.df.index[idx]
