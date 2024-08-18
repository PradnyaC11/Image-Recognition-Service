import boto3

# AWS credentials and region
AWS_ACCESS_KEY_ID     = "KEY_ID"
AWS_SECRET_ACCESS_KEY = "SECRET_KEY"
AWS_REGION = 'us-east-1'

# Initialize SQS client
sqs = boto3.client('sqs',
                   aws_access_key_id=AWS_ACCESS_KEY_ID,
                   aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                   region_name=AWS_REGION)

# Create an SQS queue
def create_queue(queue_name):
    response = sqs.create_queue(
        QueueName=queue_name
    )
    print(f"Created queue: {response['QueueUrl']}")
    return response['QueueUrl']


if __name__ == "__main__":
    # Define queue name
    req_queue_name = 'req-queue'
    resp_queue_name = 'resp-queue'

    # Create the queue
    req_queue_url = create_queue(req_queue_name)

    resp_queue_url = create_queue(resp_queue_name)

