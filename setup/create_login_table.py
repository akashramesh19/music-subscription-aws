import boto3
from botocore.exceptions import ClientError

AWS_REGION = 'us-east-1'
TABLE_NAME = 'login'

LOGIN_DATA = [
    {"email": "s4123170@student.rmit.edu.au", "user_name": "AbdulRahman", "password": "012345"},
    {"email": "s4123171@student.rmit.edu.au", "user_name": "AbdulRahman1", "password": "123456"},
    {"email": "s4123172@student.rmit.edu.au", "user_name": "AbdulRahman2", "password": "234567"},
    {"email": "s4123173@student.rmit.edu.au", "user_name": "AbdulRahman3", "password": "345678"},
    {"email": "s4123174@student.rmit.edu.au", "user_name": "AbdulRahman4", "password": "456789"},
    {"email": "s4123175@student.rmit.edu.au", "user_name": "AbdulRahman5", "password": "567890"},
    {"email": "s4123176@student.rmit.edu.au", "user_name": "AbdulRahman6", "password": "678901"},
    {"email": "s4123177@student.rmit.edu.au", "user_name": "AbdulRahman7", "password": "789012"},
    {"email": "s4123178@student.rmit.edu.au", "user_name": "AbdulRahman8", "password": "890123"},
    {"email": "s4123179@student.rmit.edu.au", "user_name": "AbdulRahman9", "password": "901234"},
]

def create_login_table(dynamodb):
    """Create the login table with email as partition key."""
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'email', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'email', 'AttributeType': 'S'}
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

def populate_login_table(table):
    """Insert all 10 login entries."""
    print(f"\nPopulating '{TABLE_NAME}' table...")
    for user in LOGIN_DATA:
        table.put_item(Item=user)
        print(f"  Added: {user['email']} | {user['user_name']} | {user['password']}")
    print(f"\nSuccessfully inserted {len(LOGIN_DATA)} users.")

def verify_table(table):
    """Verify all entries were inserted correctly."""
    print("\nVerifying table contents...")
    response = table.scan()
    items = response.get('Items', [])
    print(f"Total items in table: {len(items)}")
    for item in items:
        print(f"  {item['email']} | {item['user_name']} | {item['password']}")

def main():
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = create_login_table(dynamodb)
    populate_login_table(table)
    verify_table(table)
    print("\nDone! Login table is ready.")

if __name__ == '__main__':
    main()