import boto3
import time

# AWS credentials
AWS_ACCESS_KEY_ID     = "KEY_ID"
AWS_SECRET_ACCESS_KEY = "SECRET_KEY"
AWS_REGION = 'us-east-1'
REQ_SQS_QUEUE_URL = 'REQ_QUEUE_URL'

# Initialize boto3 SQS client
sqs_client = boto3.client(
    'sqs',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

ec2_client = boto3.client(
    'ec2',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

AMI_ID = "ami-02265762fe2923e60"    # app-tier AMI
key_pair_name = 'EC2KeyPair'

# Define scaling policies
SCALE_OUT_THRESHOLD = 0  # Example threshold for scaling out (increase capacity)
SCALE_IN_THRESHOLD = 20    # Example threshold for scaling in (decrease capacity)

# Scale out action
def scale_out(num, running_instances):
    instances_to_spin = min(21, num+1)
    print("Scaling out - adding more resources - " + str(instances_to_spin-1))
    for i in range(running_instances+1, instances_to_spin): 
        instance_name = "app-tier-instance-"+str(i)
        instances = ec2_client.run_instances(
           ImageId=AMI_ID,
           MinCount=1,
           MaxCount=1,
           InstanceType="t2.micro",
           KeyName=key_pair_name,
           TagSpecifications=[{'ResourceType':'instance',
                               'Tags': [{
                                'Key': 'Name',
                                'Value': instance_name }]}])
        print(instances['Instances'][0]['InstanceId'] + " instance created.")

# Scale in action
def scale_in(instances):
    print("Scaling in - reducing resources - "+ str(len(instances)))

    response = sqs_client.get_queue_attributes(
            QueueUrl=REQ_SQS_QUEUE_URL,
            AttributeNames=['ApproximateNumberOfMessages']
        )
    num_messages = int(response['Attributes']['ApproximateNumberOfMessages'])
    if num_messages >0:
        return    
    # print(instances)
    instance_ids = []
    for instance in instances:
        print(instance['InstanceId'])
        instance_ids.append(instance['InstanceId'])
    response = ec2_client.terminate_instances(InstanceIds=instance_ids)

    # Print termination status
    for instance in response['TerminatingInstances']:
        print(f"Instance {instance['InstanceId']} termination status: {instance['CurrentState']['Name']}")


def get_running_instances_count():
    response = ec2_client.describe_instances(
        Filters=[
            {
                'Name': 'instance-state-name',
                'Values': ['running', 'pending']
            }
        ]
    )
    pattern = "app-tier-instance-"
    # Extract instance information
    instances = [instance for reservation in response['Reservations'] for instance in reservation['Instances'] if 'Tags' in instance for tag in instance['Tags'] if tag['Key'] == 'Name' and pattern in tag['Value']]
    return instances


# Monitor the number of messages in the SQS queue
def monitor_queue():
    while True:
        try:
            # Get approximate number of messages in the queue
            response = sqs_client.get_queue_attributes(
                QueueUrl=REQ_SQS_QUEUE_URL,
                AttributeNames=['ApproximateNumberOfMessages']
            )
            num_messages = int(response['Attributes']['ApproximateNumberOfMessages'])
            running_instances = get_running_instances_count()
            running_instances_count = len(running_instances)

            print(str(num_messages) + "  " + str(running_instances_count))
            # Determine scaling action based on the number of messages
            if num_messages > running_instances_count and running_instances_count<=20:
                scale_out(num_messages-running_instances_count, running_instances_count)
            elif num_messages == 0 and running_instances_count!=0:
                time.sleep(30)
                scale_in(running_instances)
            else:
                print("No scaling action needed")
            
            time.sleep(20)  # Polling interval
        except Exception as e:
            print(f"Failed to monitor queue: {str(e)}")

# Entry point
if __name__ == "__main__":
    monitor_queue()

