from glob import glob

import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import torch
from PIL import Image
from keras.preprocessing import image
from torch.nn import functional as F
from torchvision import transforms

images=glob('images/*.png')

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

state = torch.load('results/checkpoint')
model=state['model']
model.eval()

#select image
#valid values: images/00007061_008.png images/00003989_009.png images/00001876_000.png images/00009863_041.png
selectedImage=np.random.choice(images)

print("selectedImage:{}".format(selectedImage))
plt.imshow(image.load_img(selectedImage))
plt.show()



def asTensor(image):   
    tensor = preprocess(image)
    tensor=tensor.unsqueeze(0).cuda()
    return tensor
    
def processImage(selectedImage):
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    preprocess = transforms.Compose([transforms.Resize((224,224)),transforms.ToTensor(),normalize])
    image = Image.open(selectedImage)
    image = image.convert('RGB')    
    return image

def calcHeatMap(feature_conv, weight_softmax, classId):
    print("feature_conv.shape : {}".format(feature_conv.shape))
    bz, nc, h, w = feature_conv.shape
    output_cam = []
    for i in [classId]:
        cam = weight_softmax[i].dot(feature_conv.reshape((nc, h*w)))
        cam = cam.reshape(h, w)
        cam = cam - np.min(cam)
        camOut = cam / np.max(cam)
        camOut = np.uint8(255 * camOut)       
    return camOut


#capture last Conv layer ( Batch norm 1,1024,7,7)
lastConvLayer=model._modules.get('features')[-1]
capturedFeatures = []
def onModelUpdate(module, input, output):
    capturedFeatures.append(output.data.cpu().numpy())
    
lastConvLayer.register_forward_hook(onModelUpdate)


softmaxWeights = np.squeeze(list(model.parameters())[-2].data.cpu().numpy())
print("softmaxWeights:{}".format(softmaxWeights.shape))


image=processImage(selectedImage)
modelOutput = model(asTensor(image))


probs = F.softmax(modelOutput, dim=1).data.cpu().numpy().squeeze()

print("probs shape: {}".format(probs.shape))
# print("probs: {}".format(h_x))

classId = np.argmax(probs)
print("classId : {}".format(classId))

classes = [
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
predictedClassName=classes[classId]
# print("Predicted class name: {}".format(predictedClassName))


cam = calcHeatMap(capturedFeatures[0], softmaxWeights, classId)

# print("cam.shape:{}".format(cam.shape))


cam=sp.ndimage.zoom(cam,(32,32),order=1)
fig, (ax1,ax2) = plt.subplots(nrows=1, ncols=2, sharex=True)
ax1.imshow(image)
ax1.set_title("Input")
ax2.imshow(image,alpha=1)
ax2.imshow(cam,cmap='jet',alpha=0.5)
ax2.set_title("CAM")
fig.show()
fig.suptitle("Class Activation Map (CAM) \n Detected: {}".format(predictedClassName))
fig.savefig('results/cam.png')


