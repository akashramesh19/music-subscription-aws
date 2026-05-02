import boto3
from botocore.exceptions import ClientError

AWS_REGION = 'us-east-1'
TABLE_NAME = 'subscriptions'

def create_subscriptions_table(dynamodb):
    """
    Create subscriptions table.

    Key schema:
      PK : email        (String) - the logged-in user
      SK : title#album  (String) - prevents duplicate subscription per user

    GSI  artist-index : PK=artist
      → enables querying all subscriptions for a given artist across users,
        e.g. "how many users are subscribed to Taylor Swift"
        without scanning the full table
    """
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'email',       'KeyType': 'HASH'},
                {'AttributeName': 'title#album', 'KeyType': 'RANGE'},
            ],
            AttributeDefinitions=[
                {'AttributeName': 'email',       'AttributeType': 'S'},
                {'AttributeName': 'title#album', 'AttributeType': 'S'},
                {'AttributeName': 'artist',      'AttributeType': 'S'},
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'artist-index',
                    'KeySchema': [
                        {'AttributeName': 'artist', 'KeyType': 'HASH'},
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
            print(f"Table '{TABLE_NAME}' already exists.")
            return dynamodb.Table(TABLE_NAME)
        raise

def main():
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    create_subscriptions_table(dynamodb)
    print("\nDone! Subscriptions table is ready.")

if __name__ == '__main__':
    main()
