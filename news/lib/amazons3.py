import boto3 as boto3
from flask import current_app

s3 = boto3.resource('s3',
                    aws_access_key_id="AKIAJBQML6MMYVG4OKHA",
                    aws_secret_access_key="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")


def upload_to_s3(file, filename):
    s3.Bucket(current_app.config['S3_BUCKET']).put_object(Key=filename, Body=file, ACL='public-read')
