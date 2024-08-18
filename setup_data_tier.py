import boto3
import os

# AWS credentials and region
AWS_ACCESS_KEY_ID     = "KEY_ID"
AWS_SECRET_ACCESS_KEY = "SECRET_KEY"
AWS_REGION = 'us-east-1'

# Initialize S3 client
s3 = boto3.client('s3', 
                  aws_access_key_id=AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                  region_name=AWS_REGION)

def create_bucket(bucket_name):
    response = s3.create_bucket(
        Bucket=bucket_name
    )
    print(f"Created bucket: {bucket_name}")

if __name__ == "__main__":
    # Define input and output bucket names
    input_bucket_name = 'in-bucket'
    output_bucket_name = 'out-bucket'

    # Create input bucket
    create_bucket(input_bucket_name)

    # Create output bucket
    create_bucket(output_bucket_name)

