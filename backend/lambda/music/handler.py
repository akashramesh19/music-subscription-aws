import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

dynamodb      = boto3.resource('dynamodb', region_name='us-east-1')
music_table   = dynamodb.Table('music')
sub_table     = dynamodb.Table('subscriptions')

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


# ── GET /music?artist=&title=&year=&album= ────────────────────────────────────
def get_music(params):
    artist = params.get('artist', '').strip()
    title  = params.get('title',  '').strip()
    year   = params.get('year',   '').strip()
    album  = params.get('album',  '').strip()

    try:
        # Use Query (efficient) when artist is provided
        if artist:
            result = music_table.query(
                KeyConditionExpression=Key('artist').eq(artist)
            )
            items = result.get('Items', [])
        else:
            # Fall back to Scan only when no partition key is available
            result = music_table.scan()
            items  = result.get('Items', [])

        # Apply in-memory filters for remaining attributes
        if title:
            items = [i for i in items if title.lower() in i.get('title', '').lower()]
        if year:
            items = [i for i in items if i.get('year', '') == year]
        if album:
            items = [i for i in items if album.lower() in i.get('album', '').lower()]

        return response(200, {'songs': items})

    except ClientError as e:
        return response(500, {'message': 'Database error', 'error': str(e)})


# ── GET /subscriptions?email= ─────────────────────────────────────────────────
def get_subscriptions(email):
    if not email:
        return response(400, {'message': 'email is required'})
    try:
        result = sub_table.query(
            KeyConditionExpression=Key('email').eq(email)
        )
        return response(200, {'subscriptions': result.get('Items', [])})
    except ClientError as e:
        return response(500, {'message': 'Database error', 'error': str(e)})


# ── POST /subscribe ───────────────────────────────────────────────────────────
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


# ── DELETE /unsubscribe ───────────────────────────────────────────────────────
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


# ── Router ────────────────────────────────────────────────────────────────────
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
