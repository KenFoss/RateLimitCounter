from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

# Global variable to store the counter value
counter = 0
last_reset_date = datetime.now().date()

@app.route('/')
def index():
    global counter, last_reset_date
    
    # Check if it's a new day, if so, reset the counter
    if last_reset_date != datetime.now().date():
        counter = 0
        last_reset_date = datetime.now().date()
    
    # Increment the counter
    counter += 1
    
    # If the counter reaches 100, send "Access Denied"
    if counter > 100:
        return jsonify({"message": "Access Denied"}), 403
    
    # Otherwise, return the current count
    return jsonify({"count": counter})

if __name__ == '__main__':
    app.run(debug=True)
