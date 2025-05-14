import boto3
import uuid
from django.conf import settings

s3 = boto3.client("s3",
                  aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                  region_name=settings.AWS_S3_REGION_NAME)


def upload_image_to_s3(file, folder="blogs"):
    extension = file.name.split('.')[-1]
    filename = f"{folder}/{uuid.uuid4()}.{extension}"
    s3.upload_fileobj(file, settings.AWS_STORAGE_BUCKET_NAME, filename,
                      ExtraArgs={"ACL": "public-read", "ContentType": file.content_type})
    url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{filename}"
    return url


def delete_image_from_s3(image_url):
    bucket_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/"
    key = image_url.replace(bucket_url, "")
    s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)
