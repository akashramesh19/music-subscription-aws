import boto3
import json
import requests
import os
from botocore.exceptions import ClientError


AWS_REGION  = 'us-east-1'
BUCKET_NAME = 'music-app-images-yourstudentnumber'  # Change this
JSON_FILE   = '2026a2_songs.json'

def create_bucket(s3):
    try:
        if AWS_REGION == 'us-east-1':
            s3.create_bucket(Bucket=BUCKET_NAME)
        else:
            s3.create_bucket(
                Bucket=BUCKET_NAME,
                CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
            )
        print(f"Bucket '{BUCKET_NAME}' created.")
    except ClientError as e:
        code = e.response['Error']['Code']
        if code in ('BucketAlreadyOwnedByYou', 'BucketAlreadyExists'):
            print(f"Bucket '{BUCKET_NAME}' already exists.")
        else:
            raise

def get_unique_image_urls(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    songs = data.get('songs', data) if isinstance(data, dict) else data

    # Map: filename -> url (deduplicated by filename)
    url_map = {}
    for song in songs:
        url = song.get('img_url', song.get('image_url', '')).strip()
        if url:
            filename = url.split('/')[-1]  # e.g. TaylorSwift.jpg
            url_map[filename] = url

    print(f"Found {len(url_map)} unique artist images to download.")
    return url_map

def download_and_upload(s3, url_map):
    success = 0
    failed  = 0

    for filename, url in url_map.items():
        try:
            print(f"  Downloading: {filename} from {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Upload to S3
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=f"images/{filename}",
                Body=response.content,
                ContentType='image/jpeg'
            )
            print(f"  Uploaded: images/{filename}")
            success += 1

        except Exception as e:
            print(f"  ERROR with {filename}: {e}")
            failed += 1

    print(f"\nUpload complete: {success} succeeded, {failed} failed.")

def make_bucket_public(s3_client):
    policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{BUCKET_NAME}/*"
        }]
    })
    try:
        s3_client.put_public_access_block(
            Bucket=BUCKET_NAME,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': False,
                'IgnorePublicAcls': False,
                'BlockPublicPolicy': False,
                'RestrictPublicBuckets': False
            }
        )
        s3_client.put_bucket_policy(Bucket=BUCKET_NAME, Policy=policy)
        print(f"Bucket '{BUCKET_NAME}' is now publicly readable.")
    except Exception as e:
        print(f"Could not set public policy: {e}")
        print("You may need to set this manually in the console.")

def main():
    s3_resource = boto3.resource('s3', region_name=AWS_REGION)
    s3_client   = boto3.client('s3',   region_name=AWS_REGION)

    create_bucket(s3_resource)
    make_bucket_public(s3_client)

    url_map = get_unique_image_urls(JSON_FILE)
    download_and_upload(s3_client, url_map)

    print(f"\nDone! Images are at:")
    print(f"  https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/images/<filename>")

if __name__ == '__main__':
    main()
