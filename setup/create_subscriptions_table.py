import boto3
from botocore.exceptions import ClientError

AWS_REGION = 'us-east-1'
TABLE_NAME = 'subscriptions'

def create_subscriptions_table(dynamodb):
    """
    Create subscriptions table.
    
    Schema:
      Partition Key : email        (String) - the logged-in user
      Sort Key      : title#album  (String) - matches music table sort key
                                             ensures a user can't subscribe
                                             to the same song+album twice
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
