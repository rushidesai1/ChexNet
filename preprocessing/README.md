# ChestXray preprocessing:

 Data set has high resolution images which are not suitable as input to the model. Using a high resolution image
 significantly increases the number of input feature vectors which would require an increase in the model complexity
 and training time. Also, our strategy is to use pre-trained DenseNet with ImageNet weights, so we need to use the
 same number of input features. Data set images were preprocessed before training using Apache Spark which is a
 scalable big data processing technology. Several down-sampling techniques were tried to reduce image size. 
 
 This Scala/Spark module accepts a set of images with high resolution and labels. It down samples each image to a low resolution 224*224( via bilinear Interplotation), and performs horizontal flipping as a form of data Augmentation. 
 The module allowed us to save to different environments (Local as image files and on HDFS as text files) during experimentation. 
 Module output was used to train the final model on AWS Sage Maker (PyTorch).

#Running instruction:

- Make sure you clean up the output directory contents (output/labels and output/images)
- Run the main method of App.scala

# input:
    - images directory contains high resultion images (images/input/train/*)
        - A small subset of data set, suitable size for Canvas   
    - labels/train.csv contains the 14 labels for each input image
    
#output :
    - Downsampled images (224*224) and flipped versions is stored in two formats:
        - image files (suitable for local mode)
        - Text file for each RDD image partition: Format is image label , image content ( suitable for HDFS/S3 storage)
    - New labels:
        - For each original image and its flipping has the same labels. Saved as .csv files under output/labels
        

# Requirements:
The module uses the image data source which was introduced to Spark API v2.4+. Submitting the job to a Spark cluster assumes a matching version.