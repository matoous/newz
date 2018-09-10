import boto3 as boto3
from flask import current_app

s3 = boto3.resource('s3',
                    aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
                    aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'])


def upload_to_s3(file, filename):
    s3.Bucket(current_app.config['S3_BUCKET']).put_object(Key=filename, Body=file, ACL='public-read')
