from flask import Flask, request, jsonify
from cs50 import SQL

app = Flask(__name__)

# Initialize SQLite database
db = SQL("sqlite:///database.db")

# Sign up a new user and assign them to a group
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    attributes = data.get('attributes')
    if not attributes:
        return jsonify({"error": "Attributes are required"}), 400

    # Serialize attributes for comparison
    attributes_str = ','.join(sorted(attributes))

    # Check if a matching group already exists
    group = None
    groups = db.execute("SELECT * FROM groups")
    for g in groups:
        group_attributes = [attr.strip() for attr in g["members"].split(',')]
        if any(attr in group_attributes for attr in attributes):  # Simple matching logic
            group = g
            break

    # If no matching group found, create a new one
    if not group:
        new_group_id = db.execute("INSERT INTO groups (members) VALUES (?)", attributes_str)
        group = {"id": new_group_id, "members": attributes_str}

    # Add user to the group
    user_id = db.execute("INSERT INTO users (attributes, group_id) VALUES (?, ?)", attributes_str, group["id"])
    return jsonify({"user_id": user_id, "group_id": group["id"]}), 201


# Sign in an existing user
@app.route('/signin', methods=['POST'])
def signin():
    data = request.json
    user_id = data.get('user_id')
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"message": "Sign-in successful", "user_id": user_id}), 200