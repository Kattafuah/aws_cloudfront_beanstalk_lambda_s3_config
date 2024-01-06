import os
import boto3

def lambda_handler(event, context):
    # Get environment variables
    eb_application_name = os.environ['EB_APPLICATION_NAME']
    eb_environment_name = os.environ['EB_ENVIRONMENT_NAME']
    s3_bucket_name = os.environ['S3_BUCKET_NAME']
    code_suffix = os.environ['CODE_SUFFIX']
    code_prefix = os.environ['CODE_PREFIX']

    # Create an S3 client
    s3 = boto3.client('s3')

    # Create an Elastic Beanstalk client
    eb = boto3.client('elasticbeanstalk')

    # Iterate through each record in the event (S3 trigger)
    for record in event['Records']:
        # Get the key (file path) of the S3 object
        key = record['s3']['object']['key']

        # Check if the key has a prefix of "code_" and is a .zip file
        if not (key.startswith(code_prefix) and key.endswith(code_suffix)):
            print(f'Object with key {key} does not match the required prefix and file type. Skipping deployment.')
            continue  # Skip to the next iteration if the criteria are not met #return

        # Download the file from S3 to /tmp directory in Lambda
        local_file_path = f'/tmp/{key}'
        s3.download_file(s3_bucket_name, key, local_file_path)

         # Generate a unique version label based on the file's content (MD5 hash)
        with open(local_file_path, 'rb') as file:
            file_content = file.read()
            version_label = hashlib.md5(file_content).hexdigest()[:16]

        # Generate a unique version label based on the file's MD5 hash
        #version_label = hashlib.md5(key.encode('utf-8')).hexdigest()[:16]

        # Deploy the file to Elastic Beanstalk
        response = eb.create_deploy(
            ApplicationName=eb_application_name,
            #EnvironmentName=eb_environment_name,
            VersionLabel=version_label,
            Description=f'Application version for {version_label}',
            SourceBundle={ 'S3Bucket': s3_bucket_name, 'S3Key': key },
            Process=True
        )

        # Deploy the updated application version to Elastic Beanstalk
        response = eb.create_deploy(
            ApplicationName=eb_application_name,
            EnvironmentName=eb_environment_name,
            VersionLabel=version_label
        )

        print(f'Deployment initiated with version label {version_label} for file {key}: {response}')

        # Print the deployment response
        #print(f'Deployment initiated: {response}')

    return {
        'statusCode': 200,
        'body': 'Deployment initiated successfully!'
    }
