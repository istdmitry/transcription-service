import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class S3Client:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL
        )
        self.bucket = settings.S3_BUCKET_NAME

    def upload_file(self, file_obj, object_name: str, content_type: str = None) -> str:
        """Upload a file-like object to S3."""
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
                
            self.s3.upload_fileobj(file_obj, self.bucket, object_name, ExtraArgs=extra_args)
            
            # Return the URL (assuming standard AWS S3, might need adjustment for R2/MinIO)
            # For private buckets, we should return the object key and generate presigned URLs for access
            return object_name
        except ClientError as e:
            logger.error(f"S3 Upload Error: {e}")
            raise e

    def generate_presigned_url(self, object_name: str, expiration=3600) -> str:
        """Generate a presigned URL to share an S3 object."""
        try:
            response = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': object_name},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            logger.error(f"S3 Presign Error: {e}")
            return None

    
    def delete_file(self, object_name: str):
        """Delete a file from S3."""
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=object_name)
            logger.info(f"Deleted S3 object: {object_name}")
        except ClientError as e:
            logger.error(f"S3 Delete Error: {e}")
            raise e

s3_client = S3Client()
