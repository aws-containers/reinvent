#!/usr/bin/env python3
"""
Utility script to delete the S3 bucket used by the MCP gateway setup.
This script will delete all objects in the bucket and then delete the bucket itself.

Usage:
    uv run python delete_s3_bucket.py [bucket_name]

If no bucket_name is provided, it will use the default naming pattern:
agentcore-gateway-{ACCOUNT_ID}-{REGION}
"""

import sys
import boto3
from botocore.exceptions import ClientError

# Try relative import first, fall back to absolute import
try:
    from . import utils
except ImportError:
    import utils

def delete_all_objects_in_bucket(s3_client, bucket_name):
    """Delete all objects in the bucket"""
    try:
        print(f"🗑️  Listing objects in bucket '{bucket_name}'...")

        # List all objects in the bucket
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name)

        objects_to_delete = []
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    objects_to_delete.append({'Key': obj['Key']})
                    print(f"  📄 Found object: {obj['Key']}")

        if not objects_to_delete:
            print("✅ No objects found in bucket")
            return True

        print(f"🗑️  Deleting {len(objects_to_delete)} objects...")

        # Delete objects in batches (max 1000 per batch)
        for i in range(0, len(objects_to_delete), 1000):
            batch = objects_to_delete[i:i+1000]
            delete_response = s3_client.delete_objects(
                Bucket=bucket_name,
                Delete={
                    'Objects': batch,
                    'Quiet': False
                }
            )

            # Check for errors
            if 'Errors' in delete_response:
                for error in delete_response['Errors']:
                    print(f"❌ Error deleting {error['Key']}: {error['Message']}")
                return False

            if 'Deleted' in delete_response:
                for deleted in delete_response['Deleted']:
                    print(f"✅ Deleted: {deleted['Key']}")

        print("✅ All objects deleted successfully")
        return True

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"✅ Bucket '{bucket_name}' does not exist")
            return True
        else:
            print(f"❌ Error listing/deleting objects: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error deleting objects: {e}")
        return False

def delete_bucket(s3_client, bucket_name):
    """Delete the S3 bucket"""
    try:
        print(f"🗑️  Deleting bucket '{bucket_name}'...")
        s3_client.delete_bucket(Bucket=bucket_name)
        print(f"✅ Successfully deleted bucket '{bucket_name}'")
        return True

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"✅ Bucket '{bucket_name}' does not exist")
            return True
        elif error_code == 'BucketNotEmpty':
            print(f"❌ Bucket '{bucket_name}' is not empty. This shouldn't happen after deleting objects.")
            return False
        else:
            print(f"❌ Error deleting bucket: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error deleting bucket: {e}")
        return False

def main():
    # Initialize AWS clients
    session = boto3.session.Session()
    sts_client = session.client('sts')
    s3_client = boto3.client('s3')

    # Get AWS account ID and region
    account_id = sts_client.get_caller_identity()["Account"]
    region = utils.get_current_region()

    # Check if bucket name was provided as argument
    if len(sys.argv) > 1:
        bucket_name = sys.argv[1]
        print(f"Using provided bucket name: {bucket_name}")
    else:
        # Use default naming pattern
        bucket_name = f'agentcore-gateway-{account_id}-{region}'
        print(f"Using default bucket name: {bucket_name}")

    print(f"🚀 Starting S3 bucket deletion process...")
    print(f"📍 Account ID: {account_id}")
    print(f"📍 Region: {region}")
    print(f"🪣 Bucket: {bucket_name}")
    print()

    # Step 1: Delete all objects in the bucket
    if not delete_all_objects_in_bucket(s3_client, bucket_name):
        print("❌ Failed to delete objects. Aborting bucket deletion.")
        sys.exit(1)

    # Step 2: Delete the bucket itself
    if not delete_bucket(s3_client, bucket_name):
        print("❌ Failed to delete bucket.")
        sys.exit(1)

    print()
    print("🎉 S3 bucket deletion completed successfully!")
    print(f"✅ Bucket '{bucket_name}' and all its contents have been deleted.")

if __name__ == "__main__":
    main()
