## Training

We did our training on Sagemaker. However, due to cost reasons we have closed down the instance.

Steps to run training:

1. To reproduce the results, use the following [link](https://colab.research.google.com/drive/1YexphDBE2YU4Qj6q3IQtN7ckZcHcTQkD#scrollTo=XCr8Ctc42HOV)

2. In the second last cell, you can change the # of images you want during train, validation and test phase and any other parameter you want to change.
3. The labels csv file is checked in github. We didnt check into some public repo since that was one of the requirement not put the data into public. Here are the steps to get a workable url for fetch label file.
    
    a. Copy past the following url in browser, https://github.gatech.edu/gist/rdesai65/e127e4cade5054eaadc8f886c7223e0a
    
    b. Click on "raw" and copy the url you get.
    
    c. Click on "Fetch Labels" section. Replace the existing url in !wget with the url you copied in previous step.
 
 4. Currently due to some bug, the execution fails on first run if there is not GPU. If you are running the code on GPU everything work in first go. If your one CPU then we recommend to first all cells with train_sampled=1, val_sampled=1, test_sampled=1 and EPOCH=1
 
 5. Run All cells
