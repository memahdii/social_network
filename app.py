from flask import Flask, request, jsonify
from cs50 import SQL
from flask_caching import Cache
from rq import Queue
from redis import Redis
import time
import secrets

app = Flask(__name__)

# Configure Cache
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_HOST'] = 'localhost'
app.config['CACHE_REDIS_PORT'] = 6379
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
cache = Cache(app) # Connect Flask with Redis.

# Initialize SQLite database
db = SQL("sqlite:///database.db")

# Configure Redis for queueing
redis_conn = Redis(host='localhost', port=6379) # Establishes a connection to a Redis server.
task_queue = Queue(connection=redis_conn) # create a queue object connected to the Redis instance.


# Helper function: search for a matching group where at least one attribute matches.
def find_matching_group(attributes):
    # convert attrbutes to set
    attributes_set = set(attributes)
    # check if the groups are already cached
    groups = cache.get('groups')
    if not groups:
        # query the database
        groups = db.execute("SELECT * FROM groups")
        # store the result in the cache
        cache.set('groups', groups)

    for group in groups:
        group_attributes = set(group["members"].split(','))
        if attributes_set & group_attributes:  # Check for intersection
            return group

    return None


# Queue Task: Create a new group asynchronously
def create_group_and_assign_user(attributes_str):
    new_group_id = db.execute("INSERT INTO groups (members) VALUES (?)", attributes_str)
    return {"id": new_group_id, "members": attributes_str}


# Sign up a new user and assign them to a group
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    attributes = data.get('attributes')
    if not attributes:
        return jsonify({"error": "Attributes are required"}), 400

    # Serialize attributes for comparison
    attributes_str = ','.join(sorted(attributes))

    # search for a matching group
    group = find_matching_group(attributes)

    # If no matching group found, a new group is created asynchronously
    if not group:
        # Redis stores the task details, and a worker (running separately) picks up the task for execution.
        job = task_queue.enqueue(create_group_and_assign_user, attributes_str)
        while not job.result:  # Wait for the task to complete
            time.sleep(0.1)
        group = job.result

    # Add user to the group
    user_id = db.execute("INSERT INTO users (attributes, group_id) VALUES (?, ?)", attributes_str, group["id"])
    return jsonify({"user_id": user_id, "group_id": group["id"]}), 201


@app.route('/signin', methods=['POST'])
def signin():
    data = request.json
    user_id = data.get('user_id')

    # Check if the token is already cached for the user
    cached_token = cache.get(f"user_token_{user_id}")
    if cached_token:
        # If token is found in cache, return it directly
        return jsonify({"message": "Sign-in successful", "user_id": user_id, "token": cached_token}), 200

    # Fetch user data from the database
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Check if the token is already set in the database
    token = user[0]["token"]
    if token:
        # If token is already in the database but not cached, store it in cache for future use
        cache.set(f"user_token_{user_id}", token)
        return jsonify({"message": "Sign-in successful", "user_id": user_id, "token": token}), 200

    # Generate a secure random token if it doesn't exist
    token = secrets.token_hex(16)

    # Update the token in the user's record in the database
    db.execute("UPDATE users SET token = ? WHERE id = ?", token, user_id)

    # Cache the token for future requests
    cache.set(f"user_token_{user_id}", token)

    return jsonify({"message": "Sign-in successful", "user_id": user_id, "token": token}), 200


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

@app.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    new_attributes = data.get('attributes')

    if not new_attributes:
        return jsonify({"error": "New attributes are required"}), 400

    # Serialize attributes for storage
    new_attributes_str = ','.join(sorted(new_attributes))

    # Update the user's attributes in the database
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.execute("UPDATE users SET attributes = ? WHERE id = ?", new_attributes_str, user_id)
    return jsonify({"message": "User attributes updated successfully"}), 200

@app.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.execute("DELETE FROM users WHERE id = ?", user_id)
    return jsonify({"message": "User deleted successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True)
