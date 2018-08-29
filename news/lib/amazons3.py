import boto3 as boto3
from flask import current_app

s3 = boto3.resource('s3')


def upload_to_s3(file, filename):
    s3.Bucket(current_app.config['S3_BUCKET']).put_object(Key=filename, Body=file, ACL='public-read')
