# Keras in the cloud with Amazon SageMaker

## Install from Pipfile
Open a pipenv shell
`pipenv shell`

Install dependencies
`pipenv install`

## Other prerequisites
You should have `awscli` installed and configured with AWS Access key ID and Secret access key

See here for more details:
https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html

The input images of cats and dogs has already been loaded to this S3 bucket:
https://console.aws.amazon.com/s3/buckets/doug-cats-n-dogs/?region=us-east-1&tab=overview

## Train on AWS SageMaker
The following script takes about 10 minutes to:
* Start the training job
* Launch requested ML instances
* Prepare the instances for training
* Download input data
* Train
* Create model
* Create endpoint

`python aws_job.py`

(`aws_job.py` calls `cats_n_dogs.py`)


## Install from scratch
Create a local environment using Python 3.6.4
`pyenv local 3.6.4`

Open a pipenv shell
`pipenv shell`

Install Pillow, the successor to PIL
`pipenv install pillow`

Install SageMaker
`pipenv install sagemaker`

Install TensorFlow
`pipenv install tensorflow`


## Download data set
Download the data set from the following (takes ~10 minutes):
https://www.microsoft.com/en-us/download/details.aspx?id=54765


## Split data set into training and test/validation
`python dataset_to_s3.py`


## Upload the images to S3
1. Create a bucket in S3
2. Create a folder named `data`
3. Upload the training and test/validation images to S3 (takes ~5 minutes)
`aws s3 cp ./cats_n_dogs s3://{BUCKET_NAME}/data --recursive`
`aws s3 cp ./cats_n_dogs s3://doug-cats-n-dogs/data --recursive`


## KerasSageMaker
Support repository for medium article "Keras in the cloud with Amazon SageMaker"

- `cats_n_dogs.py`: the entry script which contains the 4 main functions for SageMaker.
- `dataset_to_t3.py`: the script to import prepare and send the dataset to Amazon S3.
- `aws_job.py`: the job to send work to SageMaker and try the service.

The files should be executed in the following order : `dataset_to_s3.py` and `aws_job.py`.
You can find required python libraries to install with `pip` under `requirements.txt`.

Thank you for reading !
