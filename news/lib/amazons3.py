import boto3 as boto3
from flask import current_app


class AmazonS3():
    def __init__(self):
        self.s3 = None

    def init_app(self, app):
        self.s3 = boto3.resource('s3',
                    aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
                    aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'])

    def upload_to_s3(self, file, filename):
        self.s3.Bucket(current_app.config['S3_BUCKET']).put_object(Key=filename, Body=file, ACL='public-read')

S3 = AmazonS3()