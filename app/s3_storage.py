import io
from botocore.exceptions import NoCredentialsError, ClientError
from flask_login import current_user
from flask import current_app

def upload_file_to_s3(file_obj, object_name, content_type='application/pdf'):
    """
    Uploads an in-memory file-like object to the configured S3 bucket.

    file_obj: In-memory file object (e.g., from io.BytesIO).
    object_name: The desired key/path for the object in S3.
    content_type: The MIME type of the file.
    """
    s3_client = current_app.s3_client
    bucket_name = current_app.config['S3_BUCKET_NAME']

    try:
        s3_client.upload_fileobj(
            file_obj,
            bucket_name,
            object_name,
            ExtraArgs={'ContentType': content_type}
        )
    
    except ClientError as e:
        print(f"An S3 client error occurred during upload for {object_name} by {repr(current_user)}: {e}")
        return False
    
    return True

def generate_presigned_url(object_name, response_disposition='inline', expiration=3600):
    """
    Generates a secure, time-limited URL to access a private S3 object.

    object_name: The key/path of the object in S3.
    expiration: Time in seconds for the presigned URL to remain valid.
    """
    s3_client = current_app.s3_client
    bucket_name = current_app.config['S3_BUCKET_NAME']

    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_name, 'ResponseContentDisposition': f'{response_disposition}'},
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        print(f"[S3] Failed to generate presigned URL for '{object_name}' by {repr(current_user)}: {e}")
        return None

def delete_object_from_s3(object_name):
    """
    Deletes a specific object from the configured S3 bucket.

    object_name: The key/path of the object in S3 to be deleted.
    """
    s3_client = current_app.s3_client
    bucket_name = current_app.config.get('S3_BUCKET_NAME')

    try:
        s3_client.delete_object(Bucket=bucket_name, Key=object_name)
        return True
    except ClientError as e:
        print(f"[S3] Failed to delete '{object_name}' by {repr(current_user)}: {e}")
        return False
    

def download_file_as_bytesio(object_name):
    """
    Downloads a file from S3 and returns it as an in-memory io.BytesIO object.

    object_name: The key/path of the object in S3.
    """
    s3_client = current_app.s3_client
    bucket_name = current_app.config['S3_BUCKET_NAME']
    
    try:
        # Create an in-memory bytes buffer.
        bytes_buffer = io.BytesIO()
        
        # Download the S3 object's data directly into the buffer.
        s3_client.download_fileobj(bucket_name, object_name, bytes_buffer)
        
        # Rewind the buffer to the beginning. This is crucial so that subsequent operations can read the content from the start.
        bytes_buffer.seek(0)
        
        return bytes_buffer
        
    except ClientError as e:
        # Handle cases where the file does not exist.
        if e.response['Error']['Code'] == '404':
            print(f"[S3] File not found: {object_name}")
        else:
            # Log other potential S3 errors.
            print(f"[S3] Failed to download '{object_name}' by {repr(current_user)} as bytesio: {e}")
        return None