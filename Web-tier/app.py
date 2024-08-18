from flask import Flask, request, jsonify
import boto3
import os
import base64
import time
import logging
import redis

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

AWS_ACCESS_KEY_ID     = "KEY_ID"
AWS_SECRET_ACCESS_KEY = "SECRET_KEY"
AWS_REGION = 'us-east-1'
REQ_SQS_QUEUE_URL = 'REQ_QUEUE_URL'
RESP_SQS_QUEUE_URL = 'RESP_QUEUE_URL'

sqs = boto3.client('sqs',
                   aws_access_key_id=AWS_ACCESS_KEY_ID,
                   aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                   region_name=AWS_REGION)

results_list = set({})
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def send_message_to_queue(file_path, filename):
    with open(file_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    message_attributes = {
        'filename': {
            'DataType': 'String',
            'StringValue': filename
        }
    }
    response = sqs.send_message(
        QueueUrl=REQ_SQS_QUEUE_URL,
        MessageBody=image_data,
        MessageAttributes=message_attributes
    )
    message_id = response['MessageId']
    return message_id

def receive_messages(file_name):
    try:
        timeout = 600  # Timeout in seconds
        start_time = time.time()
        while time.time() - start_time < timeout:
            keys_list = redis_client.keys('*')
            keys_list = [key.decode('utf-8') for key in keys_list]

            for key in keys_list:
                if file_name in key:
                    redis_client.delete(key)
                    return key

            for r in results_list:
                if file_name in r:
                    results_list.discard(r)
                    return r

            response = sqs.get_queue_attributes(
                QueueUrl=RESP_SQS_QUEUE_URL,
                AttributeNames=['ApproximateNumberOfMessages']
            )
            num_messages = int(response['Attributes']['ApproximateNumberOfMessages'])
            if num_messages == 0:
                logging.info("No messages available. Sleeping for 30 seconds.")
                time.sleep(30)
                continue  # Skip to the next iteration of the loop

            response2 = sqs.receive_message(
                QueueUrl=RESP_SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                VisibilityTimeout=30,
                WaitTimeSeconds=20
            )
            if 'Messages' in response2:
                for message in response2['Messages']:
                    if file_name in message['Body']:
                        logging.info("message body - " + message['Body'])
                        delete_message(message['ReceiptHandle'])
                        return message['Body']
                    else:
                        redis_client.set(message['Body'], message['Body'])
                        results_list.add(message['Body'])
                        delete_message(message['ReceiptHandle'])
            logging.info("No relevant message found. Sleeping for 30 seconds.")
            time.sleep(30)
        logging.info("Timeout reached. No relevant message found.")
        return None
    except Exception as e:
        logging.info(f"Failed to receive messages from SQS: {str(e)}")
        return None

def delete_message(receipt_handle):
    try:
        sqs.delete_message(
            QueueUrl=RESP_SQS_QUEUE_URL,
            ReceiptHandle=receipt_handle
        )
        logging.info("Message deleted from the queue.")
    except Exception as e:
        logging.info(f"Failed to delete message from SQS: {str(e)}")

@app.route("/", methods=['POST'])
def upload_file():
    if 'inputFile' not in request.files:
        return "No file uploaded", 400

    file = request.files['inputFile']
    if file.filename == '':
        return "No file selected", 400

    # directory_path = "D:\Course_Materials\Cloud_Computing\Project\Part-2"
    directory_path = "/tmp/"
    file_path = os.path.join(directory_path, file.filename)
    file.save(file_path)

    try:
        message_id = send_message_to_queue(file_path, file.filename)
        os.remove(file_path)
        logging.info("Message: Image uploaded successfully. Message ID: " + message_id)
    except Exception as e:
        return f"Failed to upload image: {str(e)}", 500

    message = receive_messages(file.filename.split(".")[0])
    if message:
        logging.info("Message Body:" + message)
        return message, 200
    else:
        return "No relevant message found", 404

if __name__ == "__main__":
    app.run(port=5000, debug=True, threaded=True)

