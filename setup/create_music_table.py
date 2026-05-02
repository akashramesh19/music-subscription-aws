import boto3
import json
from botocore.exceptions import ClientError

AWS_REGION = 'us-east-1'
TABLE_NAME = 'music'
JSON_FILE  = '2026a2_songs.json'

def create_music_table(dynamodb):
    """
    Create the music table.

    Key schema:
      PK : artist      (String)
      SK : title#album (String) - composite prevents duplicate song+album per artist

    LSI  artist-year-lsi  : PK=artist, SK=year
      → efficient range queries like "all Taylor Swift songs from 2008"
        using Query instead of Scan + in-memory filter

    GSI  year-index        : PK=year
      → efficient lookup of all songs from a specific year
        without scanning the full table
    """
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'artist',      'KeyType': 'HASH'},
                {'AttributeName': 'title#album', 'KeyType': 'RANGE'},
            ],
            AttributeDefinitions=[
                {'AttributeName': 'artist',      'AttributeType': 'S'},
                {'AttributeName': 'title#album', 'AttributeType': 'S'},
                {'AttributeName': 'year',        'AttributeType': 'S'},
            ],
            LocalSecondaryIndexes=[
                {
                    'IndexName': 'artist-year-lsi',
                    'KeySchema': [
                        {'AttributeName': 'artist', 'KeyType': 'HASH'},
                        {'AttributeName': 'year',   'KeyType': 'RANGE'},
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'year-index',
                    'KeySchema': [
                        {'AttributeName': 'year', 'KeyType': 'HASH'},
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"Creating table '{TABLE_NAME}'...")
        table.wait_until_exists()
        print(f"Table '{TABLE_NAME}' created successfully.")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table '{TABLE_NAME}' already exists, using existing table.")
            return dynamodb.Table(TABLE_NAME)
        raise

def load_songs(table, json_file):
    """Load all songs from JSON file into the music table."""
    print(f"\nLoading songs from '{json_file}'...")

    with open(json_file, 'r') as f:
        data = json.load(f)

    # Handle both {"songs": [...]} and [...] formats
    songs = data.get('songs', data) if isinstance(data, dict) else data

    print(f"Found {len(songs)} songs to load.")

    success = 0
    failed  = 0

    for song in songs:
        try:
            title  = song.get('title',   '').strip()
            artist = song.get('artist',  '').strip()
            year   = song.get('year',    '').strip()
            album  = song.get('album',   '').strip()
            # Note: JSON uses img_url, we store as image_url per spec
            image_url = song.get('img_url', song.get('image_url', '')).strip()

            table.put_item(Item={
                'artist':     artist,
                'title#album': f"{title}#{album}",  # Composite sort key
                'title':      title,
                'year':       year,
                'album':      album,
                'image_url':  image_url
            })
            success += 1
            print(f"  [{success}] Loaded: {artist} — {title} ({album})")

        except Exception as e:
            failed += 1
            print(f"  ERROR loading {song}: {e}")

    print(f"\nLoad complete: {success} succeeded, {failed} failed.")
    return success

def verify_table(table):
    """Verify the total count matches expected."""
    print("\nVerifying table contents...")
    response = table.scan(Select='COUNT')
    count = response.get('Count', 0)
    print(f"Total items in music table: {count}")
    if count == 137:
        print("Verification PASSED — all 137 songs loaded correctly.")
    else:
        print(f"WARNING — expected 137 songs but found {count}.")

def main():
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = create_music_table(dynamodb)
    load_songs(table, JSON_FILE)
    verify_table(table)
    print("\nDone! Music table is ready.")

if __name__ == '__main__':
    main()
