import boto3
import json
import requests
import os
from botocore.exceptions import ClientError


AWS_REGION  = 'us-east-1'
BUCKET_NAME = 'music-app-images-s4110587'  
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

    url_map = {}
    for song in songs:
        url = song.get('img_url', song.get('image_url', '')).strip()
        if url:
            filename = url.split('/')[-1]  
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

def ensure_bucket_private(s3_client):
    """
    Keep the bucket private (security best practice).
    Images are served via pre-signed URLs generated at request time,
    so no public access policy is required.
    """
    try:
        s3_client.put_public_access_block(
            Bucket=BUCKET_NAME,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls':       True,
                'IgnorePublicAcls':      True,
                'BlockPublicPolicy':     True,
                'RestrictPublicBuckets': True
            }
        )
        print(f"Bucket '{BUCKET_NAME}' is private (secure).")
    except Exception as e:
        print(f"Could not enforce private access block: {e}")


def generate_presigned_url(s3_client, key, expiry=3600):
    """Return a pre-signed URL for the given S3 key (valid for expiry seconds)."""
    return s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': BUCKET_NAME, 'Key': key},
        ExpiresIn=expiry
    )


def main():
    s3_resource = boto3.resource('s3', region_name=AWS_REGION)
    s3_client   = boto3.client('s3',   region_name=AWS_REGION)

    create_bucket(s3_resource)
    ensure_bucket_private(s3_client)   

    url_map = get_unique_image_urls(JSON_FILE)
    download_and_upload(s3_client, url_map)

    sample_key = f"images/{next(iter(url_map))}"
    sample_url = generate_presigned_url(s3_client, sample_key)
    print(f"\nDone! Example pre-signed URL (expires in 1 hour):")
    print(f"  {sample_url}")
    print(f"\nNote: Generate pre-signed URLs at request time in the backend,")
    print(f"  not at upload time, so they remain valid when served to the browser.")

if __name__ == '__main__':
    main()
