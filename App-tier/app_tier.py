import boto3
import time
import base64
from PIL import Image
from io import BytesIO
import os 
from face_recognition import face_match

# AWS credentials
AWS_ACCESS_KEY_ID     = "KEY_ID"
AWS_SECRET_ACCESS_KEY = "SECRET_KEY"
AWS_REGION = 'us-east-1'
REQ_SQS_QUEUE_URL = 'REQ_QUEUE_URL'
RESP_SQS_QUEUE_URL = 'RESP_QUEUE_URL'
IN_BUCKET_NAME = "in-bucket"
OUT_BUCKET_NAME = "out-bucket"

# Initialize boto3 SQS client
sqs_client = boto3.client(
    'sqs',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# Receive messages from the SQS queue
def receive_messages():
    try:
        response = sqs_client.receive_message(
            QueueUrl=REQ_SQS_QUEUE_URL,
            AttributeNames=['All', ],
            MessageAttributeNames=[ 'filename', ],
            MaxNumberOfMessages=1,    # Maximum number of messages to retrieve
            VisibilityTimeout=30,     # The duration (in seconds) that the received messages are hidden from subsequent retrieve requests
            WaitTimeSeconds=20        # The duration (in seconds) for which the call waits for a message to arrive in the queue
        )
        if 'Messages' in response:
            return response['Messages']
        else:
            return []
    except Exception as e:
        print(f"Failed to receive messages from SQS: {str(e)}")
        return []

# Process messages
def process_messages(messages):
    for message in messages:
        print("Message ID:", message['MessageId'])
        # Delete the message from the queue
        delete_message(message['ReceiptHandle'])
        if 'MessageAttributes' in message:
            file_name = message['MessageAttributes'].get('filename', {}).get('StringValue')
            if file_name:
                print("File Name:", file_name)
        decoded_image_data = base64.b64decode(message['Body'].encode('utf-8'))
        image = Image.open(BytesIO(decoded_image_data))
        directory_path = "/tmp/"
        file_path = os.path.join(directory_path, file_name)
        image.save(file_path)
        result = face_match(file_path, "/home/ubuntu/model/data.pt")[0]
        # Add image to IN bucket
        with open(file_path, "rb") as image_file:
            upload_image_to_s3(image_file, file_name)
        # Add classification result to OUT bucket
        store_classification_result(file_name.split(".")[0], result)
        # Send result to response queue
        send_message_to_queue(file_name.split(".")[0], result)
        os.remove(file_path)

def upload_image_to_s3(image_file, object_name):
    try:
        s3_client.upload_fileobj(image_file, IN_BUCKET_NAME, object_name)
    except Exception as e:
        print(f"Failed to upload image to S3: {str(e)}")

def store_classification_result(file_name, classification_result):
    s3_client.put_object(Bucket=OUT_BUCKET_NAME, Key=file_name, Body=classification_result)
    print(f"Stored classification result for {file_name} in {OUT_BUCKET_NAME}")

def send_message_to_queue(file_name, result):
    response = sqs_client.send_message(
        QueueUrl=RESP_SQS_QUEUE_URL,
        MessageBody=f"{file_name}:{result}",
    )
    message_id = response['MessageId']
    return message_id

# Delete message from SQS queue
def delete_message(receipt_handle):
    try:
        sqs_client.delete_message(
            QueueUrl=REQ_SQS_QUEUE_URL,
            ReceiptHandle=receipt_handle
        )
        print("Message deleted from the queue.")
    except Exception as e:
        print(f"Failed to delete message from SQS: {str(e)}")

# Main function to continuously poll the queue for messages
def main():
    while True:
        messages = receive_messages()
        if messages:
            process_messages(messages)
        else:
            print("No messages in the queue. Waiting for messages...")
        time.sleep(2)
# Entry point
if __name__ == "__main__":
    main()
