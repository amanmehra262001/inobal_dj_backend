import boto3
import uuid
from django.conf import settings


def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )


def upload_image_to_s3(image_file, folder, bucket):
    try:
        s3 = get_s3_client()
        ext = image_file.name.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{ext}"
        key = f"{folder}/{unique_filename}"

        s3.upload_fileobj(
            image_file,
            bucket,
            key,
            ExtraArgs={'ContentType': image_file.content_type, 'ACL': 'public-read'}
        )

        file_url = f"https://{bucket}.s3.amazonaws.com/{key}"
        return {'error':False, 'message': 'Upload successful', 'url': file_url, 'key':key}
    except Exception as e:
        return {'error':True, 'message': str(e)}


def delete_image_from_s3(bucket, image_key):
    try:
        s3 = get_s3_client()
        s3.delete_object(Bucket=bucket, Key=image_key)
        return {'error':False, 'message': f'Image `{image_key}` deleted successfully'}
    except Exception as e:
        return {'error':True, 'message': str(e)}
    

