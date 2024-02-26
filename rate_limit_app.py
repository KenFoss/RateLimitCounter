from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import boto3
from os import environ;

app = Flask(__name__)

# Define the list of allowed origins, including Postman and the specific URL
allowed_origins = [
    "http://127.0.0.1:3000",  # Postman
    "https://recipeapp2-wvxo.onrender.com"  # Specific URL
]

# Configure CORS to allow requests from the specified origins
CORS(app, resources={r"/*": {"origins": allowed_origins}})

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-2', aws_access_key_id=environ.get('ACCESS_ID'), aws_secret_access_key=environ.get('ACCESS_SECRET'))
table_name = 'RateLimitCounter'
table = dynamodb.Table(table_name)

# Global variable to store the counter value
counter = 0
last_reset_date = datetime.now().date()

def is_valid_token(token):
  # This method will ensure validity of token in request header
    return token == environ.get('X_API_KEY')

# Function to retrieve the count and last_reset_date from DynamoDB
def get_count_from_dynamodb():
    try:
        response = table.get_item(Key={'count_id': 1})
        item = response.get('Item')
        if item:
            count = item.get('count', 0)
            last_reset_date = item.get('last_reset_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        else:
            # If the item does not exist, create it with count 0 and current date
            count = 0
            last_reset_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            table.put_item(
                Item={
                    'count_id': 1,
                    'count': count,
                    'last_reset_date': last_reset_date
                }
            )
        
        return count, last_reset_date
    except boto3.client('dynamodb').exceptions.ResourceNotFoundException as e:
        # Handle the case where the item does not exist
        count = 0
        last_reset_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        table.put_item(
            Item={
                'count_id': 1,
                'count': count,
                'last_reset_date': last_reset_date
            }
        )
        return count, last_reset_date

# Function to update the count in DynamoDB
def update_count_in_dynamodb(count, current_datetime):
    # Update the count in DynamoDB
    if (count == 0):
        table.update_item(
          Key={'count_id': 1},
          UpdateExpression='SET #count = :val, #date = :date',
          ExpressionAttributeValues={':val': count, ':date': current_datetime.strftime('%Y-%m-%d %H:%M:%S')},
          ExpressionAttributeNames={'#count': 'count', '#date': 'last_reset_date'}
        )
    else:
        table.update_item(
          Key={'count_id': 1},
          UpdateExpression='SET #count = :val',
          ExpressionAttributeValues={':val': count},
          ExpressionAttributeNames={'#count': 'count'}
        )
    
# Flask route for authentication
@app.route('/api/recipe-app/auth', methods=['GET'])
def recipe_auth():
    api_token = request.headers.get('x-api-key')
    # If the proper key has not been passed, this request is unauthorized and should not continue
    if not is_valid_token(api_token):
        return jsonify({"message": "Unauthorized Access"}), 401

    # Get the current count and last updated date from DynamoDB
    counter, last_reset_date = get_count_from_dynamodb()

    # Get the current date and time
    current_datetime = datetime.now()
    current_date = current_datetime.date()
    yesterday = current_datetime - timedelta(days=1)

    if last_reset_date:
        last_reset_date = datetime.strptime(last_reset_date, '%Y-%m-%d %H:%M:%S')

        # If last updated date is more than 24 hours before today, set count to zero
        if last_reset_date <= yesterday:
            counter = 0
            print("Count reset successfully for", current_datetime.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            # Increment the count by 1
            counter += 1
            print("Count incremented successfully for", current_datetime.strftime('%Y-%m-%d %H:%M:%S'))
    else:
        # If item doesn't exist, create a new item with count 1
        counter = 1
        print("New count item created for", current_datetime.strftime('%Y-%m-%d %H:%M:%S'))

    # Update the count in DynamoDB
    update_count_in_dynamodb(counter, current_datetime)

    # If the counter reaches 100, send "Access Denied"
    if counter > 50:
        return jsonify({"message": "Access Denied. This app is rate limited daily, try again tomorrow!"}), 403
    
    AUTH_KEY = environ.get('RECIPE_APP_AUTH')
    
    # Otherwise, return the current count
    return jsonify({"auth_key": AUTH_KEY})

if __name__ == '__main__':
  app.run(debug=True)
