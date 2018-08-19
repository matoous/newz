import boto3 as boto3

s3 = boto3.resource('s3')

def upload_to_s3(file, filename):
    s3.Bucket('newspublic').put_object(Key=filename, Body=file, ACL='public-read')
