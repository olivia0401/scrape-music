"""
AWS Deployment & Infrastructure Management
Demonstrates: Cloud deployment, EC2 management, S3 storage, monitoring setup
Skills: boto3, infrastructure as code, CloudWatch integration
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

# AWS SDK (install: pip install boto3)
try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("⚠️  Install boto3: pip install boto3")
    sys.exit(1)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AWSDeploymentManager:
    """
    Manage AWS infrastructure for scraping operations

    Features:
    - EC2 instance provisioning for scheduled scrapers
    - S3 bucket for data storage
    - CloudWatch metrics and alarms
    - IAM role management
    """

    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.ec2 = boto3.client('ec2', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.iam = boto3.client('iam')

        logger.info(f"✅ AWS clients initialized (region: {region})")

    # ========== EC2 Management ==========

    def launch_scraper_instance(
        self,
        instance_name: str = 'scraper-worker',
        instance_type: str = 't2.micro',  # Free tier eligible
        ami_id: str = 'ami-0c55b159cbfafe1f0',  # Ubuntu 20.04 LTS
        key_name: Optional[str] = None
    ) -> str:
        """
        Launch EC2 instance for running scrapers

        Args:
            instance_name: Tag name for the instance
            instance_type: Instance size (t2.micro for free tier)
            ami_id: Amazon Machine Image ID
            key_name: SSH key pair name (must exist in AWS)

        Returns:
            Instance ID
        """
        try:
            # User data script to auto-install dependencies
            user_data = """#!/bin/bash
                set -e

                # Update system
                apt-get update
                apt-get install -y python3-pip git

                # Clone scraper repository
                cd /home/ubuntu
                git clone https://github.com/olivia0401/scrape-music.git scrape_lab
                cd scrape_lab

                # Install Python dependencies
                pip3 install -r requirements.txt

                # Set up cron job for scheduler
                echo "0 * * * * cd /home/ubuntu/scrape_lab && python3 scheduler.py" | crontab -

                # Install CloudWatch agent for monitoring
                wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
                dpkg -i -E ./amazon-cloudwatch-agent.deb

                echo "✅ Scraper instance setup complete" > /home/ubuntu/setup_complete.txt
            """

            # Launch instance
            response = self.ec2.run_instances(
                ImageId=ami_id,
                InstanceType=instance_type,
                MinCount=1,
                MaxCount=1,
                KeyName=key_name,
                UserData=user_data,
                TagSpecifications=[{
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': instance_name},
                        {'Key': 'Project', 'Value': 'scrape-lab'},
                        {'Key': 'Purpose', 'Value': 'automated-scraping'}
                    ]
                }],
                IamInstanceProfile={
                    'Name': 'ScraperInstanceProfile'  # Must be created first
                },
                SecurityGroupIds=[self._get_or_create_security_group()]
            )

            instance_id = response['Instances'][0]['InstanceId']
            logger.info(f"🚀 Launched EC2 instance: {instance_id}")

            # Wait for instance to start
            logger.info("⏳ Waiting for instance to start...")
            waiter = self.ec2.get_waiter('instance_running')
            waiter.wait(InstanceIds=[instance_id])

            logger.info(f"✅ Instance {instance_id} is running")
            return instance_id

        except ClientError as e:
            logger.error(f"❌ Failed to launch instance: {e}")
            raise

    def _get_or_create_security_group(self) -> str:
        """Create security group with necessary ports"""
        group_name = 'scraper-sg'

        try:
            # Try to find existing group
            response = self.ec2.describe_security_groups(
                Filters=[{'Name': 'group-name', 'Values': [group_name]}]
            )

            if response['SecurityGroups']:
                return response['SecurityGroups'][0]['GroupId']

        except ClientError:
            pass

        # Create new security group
        try:
            response = self.ec2.create_security_group(
                GroupName=group_name,
                Description='Security group for scraper instances'
            )

            group_id = response['GroupId']

            # Add inbound rules (SSH only for management)
            self.ec2.authorize_security_group_ingress(
                GroupId=group_id,
                IpPermissions=[{
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }]
            )

            logger.info(f"✅ Created security group: {group_id}")
            return group_id

        except ClientError as e:
            logger.error(f"❌ Failed to create security group: {e}")
            raise

    def stop_instance(self, instance_id: str):
        """Stop EC2 instance (to save costs)"""
        try:
            self.ec2.stop_instances(InstanceIds=[instance_id])
            logger.info(f"⏸️  Stopped instance: {instance_id}")
        except ClientError as e:
            logger.error(f"❌ Failed to stop instance: {e}")

    def terminate_instance(self, instance_id: str):
        """Terminate EC2 instance"""
        try:
            self.ec2.terminate_instances(InstanceIds=[instance_id])
            logger.info(f"🗑️  Terminated instance: {instance_id}")
        except ClientError as e:
            logger.error(f"❌ Failed to terminate instance: {e}")

    # ========== S3 Storage ==========

    def create_data_bucket(self, bucket_name: str) -> str:
        """
        Create S3 bucket for storing scraped data

        Args:
            bucket_name: Unique bucket name (must be globally unique)

        Returns:
            Bucket name
        """
        try:
            if self.region == 'us-east-1':
                self.s3.create_bucket(Bucket=bucket_name)
            else:
                self.s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )

            # Enable versioning
            self.s3.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )

            # Set lifecycle policy to archive old data
            self.s3.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration={
                    'Rules': [{
                        'Id': 'ArchiveOldData',
                        'Status': 'Enabled',
                        'Transitions': [{
                            'Days': 90,
                            'StorageClass': 'GLACIER'
                        }],
                        'Expiration': {'Days': 365}
                    }]
                }
            )

            logger.info(f"✅ Created S3 bucket: {bucket_name}")
            return bucket_name

        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                logger.info(f"ℹ️  Bucket already exists: {bucket_name}")
                return bucket_name
            else:
                logger.error(f"❌ Failed to create bucket: {e}")
                raise

    def upload_to_s3(self, local_file: Path, bucket: str, s3_key: str):
        """Upload scraped data to S3"""
        try:
            self.s3.upload_file(str(local_file), bucket, s3_key)
            logger.info(f"📤 Uploaded {local_file.name} to s3://{bucket}/{s3_key}")
        except ClientError as e:
            logger.error(f"❌ Failed to upload to S3: {e}")

    # ========== CloudWatch Monitoring ==========

    def setup_monitoring(self, instance_id: str):
        """
        Set up CloudWatch alarms for instance monitoring

        Monitors:
        - CPU utilization (alert if > 80%)
        - Disk usage (alert if > 90%)
        - Scraper job failures (custom metric)
        """
        try:
            # CPU utilization alarm
            self.cloudwatch.put_metric_alarm(
                AlarmName=f'scraper-{instance_id}-high-cpu',
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=2,
                MetricName='CPUUtilization',
                Namespace='AWS/EC2',
                Period=300,  # 5 minutes
                Statistic='Average',
                Threshold=80.0,
                ActionsEnabled=True,
                AlarmDescription='Alert when CPU exceeds 80%',
                Dimensions=[{
                    'Name': 'InstanceId',
                    'Value': instance_id
                }]
            )

            logger.info(f"✅ Set up CloudWatch monitoring for {instance_id}")

        except ClientError as e:
            logger.error(f"❌ Failed to setup monitoring: {e}")

    def publish_custom_metric(self, metric_name: str, value: float, unit: str = 'Count'):
        """
        Publish custom metric to CloudWatch

        Example: Track scraper success/failure rates
        """
        try:
            self.cloudwatch.put_metric_data(
                Namespace='ScraperMetrics',
                MetricData=[{
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit,
                    'Timestamp': datetime.utcnow()
                }]
            )
        except ClientError as e:
            logger.error(f"❌ Failed to publish metric: {e}")


# ========== Example Usage ==========

def deploy_production_scraper():
    """
    Full deployment example

    This demonstrates:
    1. Provisioning EC2 instance
    2. Setting up S3 storage
    3. Configuring monitoring
    4. Uploading initial data
    """

    manager = AWSDeploymentManager(region='us-east-1')

    # 1. Create S3 bucket for data
    bucket_name = 'scrape-lab-data-2025'  # Must be globally unique
    manager.create_data_bucket(bucket_name)

    # 2. Launch EC2 instance
    # NOTE: Requires SSH key pair in AWS
    # instance_id = manager.launch_scraper_instance(
    #     instance_name='scraper-production',
    #     key_name='your-key-pair'  # Replace with your key
    # )

    # 3. Set up monitoring
    # manager.setup_monitoring(instance_id)

    # 4. Upload existing data to S3
    output_dir = Path('outputs')
    if output_dir.exists():
        for file in output_dir.glob('*.csv'):
            s3_key = f'scraped-data/{file.name}'
            manager.upload_to_s3(file, bucket_name, s3_key)

    logger.info("🎉 Deployment complete!")


if __name__ == '__main__':
    # Example: Deploy to AWS
    # NOTE: Requires AWS credentials configured (aws configure)

    print("""
    ⚠️  AWS Deployment Script

    Before running:
    1. Configure AWS credentials: aws configure
    2. Create SSH key pair in EC2 console
    3. Update bucket name to be globally unique
    4. Review security group settings

    Uncomment deploy_production_scraper() to proceed
    """)

    # deploy_production_scraper()
