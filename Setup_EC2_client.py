import boto3
import time
import datetime

# access key of dev-iam
AWS_ACCESS_KEY_ID     = "KEY_ID"
AWS_SECRET_ACCESS_KEY = "SECRET_KEY"

key_pair_name = 'EC2KeyPair'

ec2_client = boto3.client('ec2',
      region_name='us-east-1',
      aws_access_key_id=AWS_ACCESS_KEY_ID, 
      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

def get_instance_state(instance_id):
    ec2 = boto3.client('ec2')
    response = ec2.describe_instances(InstanceIds=[instance_id])

    # Check if the instance exists
    if 'Reservations' in response and len(response['Reservations']) > 0:
        instance = response['Reservations'][0]['Instances'][0]
        state = instance['State']['Name']
        print(f"The state of instance {instance_id} is: {state}")
        return state
    else:
        print(f"Instance {instance_id} not found.")
        return None

# ami_id = "ami-00ddb0e5626798373"    # ubuntu 18.6
ami_id = "ami-07d9b9ddc6cd8dd30"      # ubuntu 22.04
# ami_id = "ami-02265762fe2923e60"    # app-tier AMI

instances = ec2_client.run_instances(
           ImageId=ami_id,
           MinCount=1,
           MaxCount=1,
           InstanceType="t2.micro",
           KeyName=key_pair_name,
           TagSpecifications=[{'ResourceType':'instance',
                               'Tags': [{
                                'Key': 'Name',
                                'Value': 'app-tier-instance-1' }]}])

instance_id = instances['Instances'][0]['InstanceId']
print('Instance ID - ', instance_id)

allocation_id = "eipalloc-0a1dbee22082087a7"

response = ec2_client.associate_address(
    InstanceId=instance_id,
    AllocationId=allocation_id
)
print("Associate Address respsonse:", response)
