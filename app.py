from flask import Flask, request, jsonify
from cs50 import SQL
from flask_caching import Cache
from redis.exceptions import RedisError

app = Flask(__name__)

# Configure Cache
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_HOST'] = 'localhost'
app.config['CACHE_REDIS_PORT'] = 6379
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
cache = Cache(app)

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

    # Cache groups lookup
    try:
        groups = cache.get('groups')
        if not groups:
            groups = db.execute("SELECT * FROM groups")
            cache.set('groups', groups)
    except RedisError:
        groups = db.execute("SELECT * FROM groups")  # Fallback if Redis fails

    # Check if a matching group already exists
    group = None
    for g in groups:
        group_attributes = [attr.strip() for attr in g["members"].split(',')]
        if any(attr in group_attributes for attr in attributes):  # Simple matching logic
            group = g
            break

    # If no matching group found, create a new one
    if not group:
        new_group_id = db.execute("INSERT INTO groups (members) VALUES (?)", attributes_str)
        group = {"id": new_group_id, "members": attributes_str}

        # Update cache with the new group
        groups.append(group)
        try:
            cache.set('groups', groups)
        except RedisError:
            pass  # Ignore cache errors

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

# Retrieve the group of a specific user
@app.route('/group/<int:user_id>', methods=['GET'])
@cache.cached(timeout=60, query_string=True)  # Cache the response for 60 seconds
def get_group(user_id):
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    group_id = user[0]["group_id"]
    group = db.execute("SELECT * FROM groups WHERE id = ?", group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404

    # Retrieve all users in the group
    group_members = db.execute("SELECT * FROM users WHERE group_id = ?", group_id)
    members = [{"id": member["id"], "attributes": member["attributes"]} for member in group_members]
    return jsonify({"group_id": group_id, "members": members}), 200
