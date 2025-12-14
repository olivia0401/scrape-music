"""
AWS Deployment for Scrapers
Demonstrates: EC2 provisioning, S3 storage, CloudWatch monitoring
Simple setup - directly answers "Spinning up EC2 instances for real-time data collection"
"""

import logging
from pathlib import Path

# AWS SDK
try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    boto3 = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AWSScraperDeployment:
    """
    Simple AWS deployment for scraping infrastructure

    Key features:
    - Launch EC2 instance for 24/7 scraping
    - Store data in S3 bucket
    - Basic CloudWatch monitoring
    """

    def __init__(self, region='us-east-1'):
        if not AWS_AVAILABLE:
            raise ImportError("Install: pip install boto3")

        self.region = region
        self.ec2 = boto3.client('ec2', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)

        logger.info(f"✅ AWS initialized (region: {region})")

    def launch_scraper_instance(self, key_name=None):
        """
        Launch EC2 instance for running scrapers

        Args:
            key_name: Your SSH key pair name (optional)

        Returns:
            instance_id
        """

        # User data: auto-install dependencies on startup
        user_data_script = """#!/bin/bash
set -e

# Update and install Python
apt-get update
apt-get install -y python3-pip git

# Clone your scraper repo
cd /home/ubuntu
git clone https://github.com/olivia0401/scrape-music.git scraper
cd scraper

# Install dependencies
pip3 install -r requirements.txt

# Run scheduler
nohup python3 scheduler.py > scraper.log 2>&1 &

echo "Scraper deployed!" > /home/ubuntu/deploy_complete.txt
"""

        try:
            response = self.ec2.run_instances(
                ImageId='ami-0c55b159cbfafe1f0',  # Ubuntu 20.04 LTS
                InstanceType='t2.micro',  # Free tier
                MinCount=1,
                MaxCount=1,
                KeyName=key_name,
                UserData=user_data_script,
                TagSpecifications=[{
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': 'scraper-worker'}]
                }]
            )

            instance_id = response['Instances'][0]['InstanceId']
            logger.info(f"🚀 EC2 instance launched: {instance_id}")
            logger.info("⏳ Waiting for instance to start...")

            # Wait for running state
            waiter = self.ec2.get_waiter('instance_running')
            waiter.wait(InstanceIds=[instance_id])

            logger.info(f"✅ Instance running: {instance_id}")
            return instance_id

        except ClientError as e:
            logger.error(f"❌ Launch failed: {e}")
            raise

    def create_data_bucket(self, bucket_name):
        """
        Create S3 bucket for storing scraped data

        Args:
            bucket_name: Must be globally unique
        """
        try:
            if self.region == 'us-east-1':
                self.s3.create_bucket(Bucket=bucket_name)
            else:
                self.s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )

            logger.info(f"✅ S3 bucket created: {bucket_name}")
            return bucket_name

        except ClientError as e:
            if 'BucketAlreadyOwnedByYou' in str(e):
                logger.info(f"ℹ️  Bucket exists: {bucket_name}")
                return bucket_name
            else:
                logger.error(f"❌ Bucket creation failed: {e}")
                raise

    def upload_data(self, local_file, bucket, s3_key):
        """Upload file to S3"""
        try:
            self.s3.upload_file(str(local_file), bucket, s3_key)
            logger.info(f"📤 Uploaded: s3://{bucket}/{s3_key}")
        except ClientError as e:
            logger.error(f"❌ Upload failed: {e}")

    def setup_monitoring(self, instance_id):
        """
        Set up basic CloudWatch alarm for CPU

        Args:
            instance_id: EC2 instance to monitor
        """
        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName=f'scraper-{instance_id}-high-cpu',
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=2,
                MetricName='CPUUtilization',
                Namespace='AWS/EC2',
                Period=300,
                Statistic='Average',
                Threshold=80.0,
                ActionsEnabled=False,  # No notifications for demo
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}]
            )

            logger.info(f"✅ CloudWatch alarm set for {instance_id}")

        except ClientError as e:
            logger.error(f"❌ Monitoring setup failed: {e}")


# ========== Example Usage ==========

def deploy_example():
    """
    Simple deployment example

    Steps:
    1. Create S3 bucket for data storage
    2. Launch EC2 instance with auto-setup
    3. Set up monitoring
    4. Upload existing data
    """

    manager = AWSScraperDeployment(region='us-east-1')

    # 1. Create bucket
    bucket_name = 'my-scraper-data-2025'  # Change this!
    manager.create_data_bucket(bucket_name)

    # 2. Launch EC2 (optional - requires SSH key)
    # instance_id = manager.launch_scraper_instance(key_name='your-key')
    # manager.setup_monitoring(instance_id)

    # 3. Upload data
    output_dir = Path('outputs')
    if output_dir.exists():
        for csv_file in output_dir.glob('*.csv'):
            s3_key = f'data/{csv_file.name}'
            manager.upload_data(csv_file, bucket_name, s3_key)

    logger.info("🎉 Deployment complete!")


if __name__ == '__main__':
    if not AWS_AVAILABLE:
        print("⚠️  Install boto3: pip install boto3")
        print("This script requires AWS SDK for Python")
    else:
        print("""
AWS Scraper Deployment

Before running:
1. Configure AWS: aws configure
2. Update bucket_name (must be globally unique)
3. Uncomment deploy_example() to run

Note: EC2 launch requires SSH key pair in AWS console
        """)

        # Uncomment to run:
        # deploy_example()
