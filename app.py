from flask import Flask, request, jsonify
from cs50 import SQL
from flask_caching import Cache
from rq import Queue
from redis import Redis
import time

app = Flask(__name__)

# Configure Cache
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_HOST'] = 'localhost'
app.config['CACHE_REDIS_PORT'] = 6379
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
cache = Cache(app)

# Initialize SQLite database
db = SQL("sqlite:///database.db")

# Configure Redis for queueing
redis_conn = Redis(host='localhost', port=6379)
task_queue = Queue(connection=redis_conn)


# Helper Function: Search for a matching group
def find_matching_group(attributes):
    """
    Efficiently find a group where at least one attribute matches.
    """
    attributes_set = set(attributes)
    groups = cache.get('groups')
    if not groups:
        groups = db.execute("SELECT * FROM groups")
        cache.set('groups', groups)

    for group in groups:
        group_attributes = set(group["members"].split(','))
        if attributes_set & group_attributes:  # Check for intersection
            return group

    return None


# Queue Task: Create a new group
def create_group_and_assign_user(attributes_str):
    """
    Create a new group and assign the user to it. Run asynchronously.
    """
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

    # Efficiently search for a matching group
    group = find_matching_group(attributes)

    # If no matching group found, enqueue the task to create a new one
    if not group:
        job = task_queue.enqueue(create_group_and_assign_user, attributes_str)
        while not job.result:  # Wait for the task to complete
            time.sleep(0.1)
        group = job.result

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


if __name__ == "__main__":
    app.run(debug=True)
