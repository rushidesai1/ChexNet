# Hello World for Spark / Scala on Amazon Elastic Map Reduce (EMR)

## Compile
sbt package


## Run remotely on Amazon EMR
1. Copy target jar file to S3
2. Create EMR cluster
    * Configure cluster with application step linking to jar

## S3 input / output
Objects in S3 bucket are used for input and output. The input has already been created at the following location:

https://console.aws.amazon.com/s3/buckets/team10-chestxray/tutorialEMR/?region=us-east-1&tab=overview


## AWS EMR Configuration

### Add steps
* Step type: Spark application
* Name: Spark Application
* Deploy mode: Cluster
* Spark-submit options: `--class SimpleApp`
* Application location: `s3://team10-chestxray/tutorialEMR/simple-project_2.10-1.0.jar`
* Arguments: <none>
* Action on failure: Terminate cluster

### General Options
* Cluster name: `SimpleApp`
* Logging: S3 folder: `s3://team10-chestxray/`
* Launch mode: Step execution

### Hardware configuration
* Change to availability zone to 1a -- other AZs might not have the desired instance type
* Instance type: m1.medium
* Number of instances: 3 (1 master and 2 core nodes)


## Run locally in bigbox Docker container to test
The following _only_ works with local files in HDFS; it does *not* work with S3 files:

`$SPARK_HOME/bin/spark-submit   --class "SimpleApp"   --master local[4]   target/scala-2.10/simple-project_2.10-1.0.jar`
