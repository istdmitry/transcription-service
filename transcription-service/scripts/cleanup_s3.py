import boto3
import os
import sys
from datetime import datetime, timezone, timedelta

# Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")

def cleanup_old_files(days=3):
    if not all([S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]):
        print("Error: Missing environment variables.")
        print("Please set: S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        print("Optional: AWS_REGION, AWS_S3_ENDPOINT_URL")
        sys.exit(1)

    print(f"Connecting to S3 Bucket: {S3_BUCKET_NAME}...")
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
        endpoint_url=AWS_S3_ENDPOINT_URL
    )

    try:
        # List objects
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=S3_BUCKET_NAME)

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        print(f"Deleting files older than: {cutoff_date}")
        
        deleted_count = 0
        total_size_freed = 0

        for page in pages:
            if 'Contents' not in page:
                continue
            
            for obj in page['Contents']:
                last_modified = obj['LastModified']
                # Ensure last_modified is timezone-aware (boto3 usually returns aware)
                
                if last_modified < cutoff_date:
                    print(f"Deleting {obj['Key']} (Last Modified: {last_modified})")
                    s3.delete_object(Bucket=S3_BUCKET_NAME, Key=obj['Key'])
                    deleted_count += 1
                    total_size_freed += obj['Size']
        
        print("-" * 40)
        print(f"Cleanup Complete.")
        print(f"Files Deleted: {deleted_count}")
        print(f"Space Freed: {total_size_freed / 1024 / 1024:.2f} MB")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cleanup old S3 files")
    parser.add_argument("--days", type=int, default=3, help="Delete files older than N days (default: 3)")
    args = parser.parse_args()
    
    cleanup_old_files(args.days)
