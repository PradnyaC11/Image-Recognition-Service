# Project Description
This project is part of CSE 546 - Cloud Computing course. 

Architecture of the application - 

![Alt text](https://github.com/PradnyaC11/Image-Recognition-Service/blob/main/architecture_diagram.png "Architecture Diagram")

The web tier will receive face recognition requests from clients and forward it to the App Tier for model inference using the SQS queue. It should also return the recognition result from the App Tier as output to the users. The input from each request is a .jpg file, and the output in each response is the recognition result.
Output would be in form of: <filename>:<classification_results>
The Web Tier also runs the autoscaling controller, which determines how to scale the App Tier. AWS autoscaling features are not used for this, instead my own auto scaling algorithm is implemented.

The App Tier will use the provided deep learning model for model inference. The App Tier should automatically scale out when the request demand increases and automatically scale in when the demand drops. The number of App Tier instances should be 0 when there are no requests being processed or waiting to be processed. The number of App Tier instances can scale to at most 20 because we have limited resources from the free tier.

Data Tier consists of two S3 buckets and stores all inputs (images) and outputs (recognition results) in separate bucket for persistence.
