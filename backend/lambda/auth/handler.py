import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('login')

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS'
}


def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body)
    }


def login(email, password):
    try:
        result = table.get_item(Key={'email': email})
    except ClientError as e:
        return response(500, {'message': 'Database error', 'error': str(e)})

    item = result.get('Item')
    if not item:
        return response(401, {'message': 'email or password is invalid'})
    if item['password'] != password:
        return response(401, {'message': 'email or password is invalid'})

    return response(200, {
        'message': 'Login successful',
        'email': item['email'],
        'user_name': item['user_name']
    })


def register(email, user_name, password):
    if not email or not user_name or not password:
        return response(400, {'message': 'email, user_name and password are required'})

    try:
        result = table.get_item(Key={'email': email})
    except ClientError as e:
        return response(500, {'message': 'Database error', 'error': str(e)})

    if result.get('Item'):
        return response(409, {'message': 'The email already exists'})

    try:
        table.put_item(Item={
            'email': email,
            'user_name': user_name,
            'password': password
        })
    except ClientError as e:
        return response(500, {'message': 'Failed to register user', 'error': str(e)})

    return response(201, {'message': 'User registered successfully', 'email': email})


def lambda_handler(event, context):

    if event.get('httpMethod') == 'OPTIONS':
        return response(200, {})

    path = event.get('path', '')
    method = event.get('httpMethod', '')

    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return response(400, {'message': 'Invalid JSON body'})

    if path == '/login' and method == 'POST':
        email = body.get('email', '').strip()
        password = body.get('password', '').strip()
        if not email or not password:
            return response(400, {'message': 'email and password are required'})
        return login(email, password)

    if path == '/register' and method == 'POST':
        return register(
            body.get('email', '').strip(),
            body.get('user_name', '').strip(),
            body.get('password', '').strip()
        )

    return response(404, {'message': 'Route not found'})
