import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

dynamodb    = boto3.resource('dynamodb', region_name='us-east-1')
music_table = dynamodb.Table('music')
sub_table   = dynamodb.Table('subscriptions')
s3_client   = boto3.client('s3', region_name='us-east-1')

BUCKET_NAME = 'music-app-images-s4110587'


def presigned_url(original_url, expiry=3600):
    """Replace stored image URL with a pre-signed S3 URL."""
    if not original_url:
        return original_url
    filename = original_url.split('/')[-1].split('?')[0]
    try:
        return s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': f'images/{filename}'},
            ExpiresIn=expiry
        )
    except Exception:
        return original_url  # fallback to original URL if S3 fails


def attach_presigned_urls(items):
    """Add pre-signed S3 image URL to each item."""
    for item in items:
        item['image_url'] = presigned_url(item.get('image_url', ''))
    return items

CORS_HEADERS = {
    'Access-Control-Allow-Origin':  '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS'
}


def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers':    CORS_HEADERS,
        'body':       json.dumps(body)
    }


# GET function
def get_music(params):
    artist = params.get('artist', '').strip()
    title  = params.get('title',  '').strip()
    year   = params.get('year',   '').strip()
    album  = params.get('album',  '').strip()

    try:
        songs = []

        # Strategy 1: artist + year -- use LSI (artist-year-index)
        # Most efficient for demo query: "Find all songs by Jimmy Buffett in 1974"
        if artist and year:
            result = music_table.query(
                IndexName='artist-year-index',
                KeyConditionExpression=Key('artist').eq(artist) & Key('year').eq(year)
            )
            songs = result.get('Items', [])
            # Case-insensitive fallback if exact match returns nothing
            if not songs:
                all_items = music_table.scan().get('Items', [])
                songs = [i for i in all_items
                         if i.get('artist', '').lower() == artist.lower()
                         and i.get('year', '') == year]

        # Strategy 2: artist only -- main table Query on PK
        elif artist:
            result = music_table.query(
                KeyConditionExpression=Key('artist').eq(artist)
            )
            songs = result.get('Items', [])
            # Case-insensitive fallback if exact match returns nothing
            if not songs:
                all_items = music_table.scan().get('Items', [])
                songs = [i for i in all_items
                         if i.get('artist', '').lower() == artist.lower()]

        # ── Strategy 3: title only → use GSI (title-year-index) ──────────────
        elif title and not year:
            result = music_table.query(
                IndexName='title-year-index',
                KeyConditionExpression=Key('title').eq(title)
            )
            songs = result.get('Items', [])

        # ── Strategy 4: title + year → use GSI with both keys ────────────────
        elif title and year:
            result = music_table.query(
                IndexName='title-year-index',
                KeyConditionExpression=Key('title').eq(title) & Key('year').eq(year)
            )
            songs = result.get('Items', [])

        # ── Strategy 5: no artist/title → Scan (last resort) ─────────────────
        else:
            result = music_table.scan()
            songs  = result.get('Items', [])

        # In-memory filter for album (no index on album)
        if album:
            songs = [s for s in songs if album.lower() in s.get('album', '').lower()]

        # In-memory year filter when year-only search
        if year and not artist and not title:
            songs = [s for s in songs if s.get('year', '') == year]

        return response(200, {'songs': attach_presigned_urls(songs)})

    except ClientError as e:
        return response(500, {'message': 'Database error', 'error': str(e)})


# GET /subscriptions?email
def get_subscriptions(email):
    if not email:
        return response(400, {'message': 'email is required'})
    try:
        result = sub_table.query(
            KeyConditionExpression=Key('email').eq(email)
        )
        return response(200, {'subscriptions': attach_presigned_urls(result.get('Items', []))})
    except ClientError as e:
        return response(500, {'message': 'Database error', 'error': str(e)})


# POST /subscribe 
def subscribe(body):
    email     = body.get('email',     '').strip()
    title     = body.get('title',     '').strip()
    album     = body.get('album',     '').strip()
    artist    = body.get('artist',    '').strip()
    year      = body.get('year',      '').strip()
    image_url = body.get('image_url', '').strip()

    if not email or not title or not album:
        return response(400, {'message': 'email, title and album are required'})

    try:
        sub_table.put_item(Item={
            'email':       email,
            'title#album': f"{title}#{album}",
            'title':       title,
            'album':       album,
            'artist':      artist,
            'year':        year,
            'image_url':   image_url
        })
        return response(201, {'message': 'Subscribed successfully'})
    except ClientError as e:
        return response(500, {'message': 'Failed to subscribe', 'error': str(e)})


# DELETE /unsubscribe 
def unsubscribe(body):
    email = body.get('email', '').strip()
    title = body.get('title', '').strip()
    album = body.get('album', '').strip()

    if not email or not title or not album:
        return response(400, {'message': 'email, title and album are required'})

    try:
        sub_table.delete_item(Key={
            'email':       email,
            'title#album': f"{title}#{album}"
        })
        return response(200, {'message': 'Unsubscribed successfully'})
    except ClientError as e:
        return response(500, {'message': 'Failed to unsubscribe', 'error': str(e)})


# Router
def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return response(200, {})

    path   = event.get('path', '')
    method = event.get('httpMethod', '')
    params = event.get('queryStringParameters') or {}

    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return response(400, {'message': 'Invalid JSON body'})

    if path == '/music' and method == 'GET':
        return get_music(params)

    if path == '/subscriptions' and method == 'GET':
        return get_subscriptions(params.get('email', ''))

    if path == '/subscribe' and method == 'POST':
        return subscribe(body)

    if path == '/unsubscribe' and method == 'DELETE':
        return unsubscribe(body)

    return response(404, {'message': 'Route not found'})