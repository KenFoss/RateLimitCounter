from flask import Flask, jsonify, request
from datetime import datetime
from os import environ;

app = Flask(__name__)

# Global variable to store the counter value
counter = 0
last_reset_date = datetime.now().date()

def is_valid_token(token):
  # This method will ensure validity of token in request header
    return token == environ.get('X_API_KEY')

@app.route('/api/recipe-app/auth', methods=['GET'])
def recipe_auth():
    global counter, last_reset_date

    api_token = request.headers.get('x-api-key')
    # If the propper key has not been passed, this request is unauthorized and should not continue
    if not (is_valid_token(api_token)) :
        return jsonify({"message": "Unauthorized Access"}), 401
    
    # Check if it's a new day, if so, reset the counter
    if last_reset_date != datetime.now().date():
        counter = 0
        last_reset_date = datetime.now().date()
    
    # Increment the counter
    counter += 1
    
    # If the counter reaches 100, send "Access Denied"
    if counter > 100:
        return jsonify({"message": "Access Denied"}), 403
    
    AUTH_KEY  = environ.get('RECIPE_APP_AUTH')
    
    # Otherwise, return the current count
    return jsonify({"auth_key": AUTH_KEY})

if __name__ == '__main__':
    app.run(debug=True)
