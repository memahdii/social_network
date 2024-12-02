# Explanation of Code  

**Database Operations**  
- Users Table:  Stores each user's attributes and their assigned group ID.

- Groups Table:  Stores a list of members in the group (denormalized for simplicity).  

**Endpoints**  
- /signup:  
  - Accepts user attributes.  
  - Matches the user to an existing group or creates a new group.  
  - Inserts the user into the users table with the corresponding group_id.  
- /signin:  
  - Verifies user existence based on their ID.  
- /group/<user_id>:  
  - Retrieves all users in the group the user belongs to by querying the users table.  


**Testing Steps**
1. Install the packages using this command `pip install -r requirements.txt` 
2. run Redis using this command in terminal `redis-server`
3. open a new terminal and run flask using this command: `flask run`
4. Start a worker process for the queue: `rq worker`  
5. Run the Testing Script: `python test_flask_app.py`  

Other options: You can use a tool like Postman or curl to interact with the endpoints
  >Sign Up:  
  `curl -X POST http://127.0.0.1:5000/signup \
  -H "Content-Type: application/json" \
  -d '{"attributes": ["Software", "Engineer", "Brussels"]}'`  
  >Sign In:  
  `curl -X POST http://127.0.0.1:5000/signin \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'`  
  >group/<user_id>:  
  `curl http://127.0.0.1:5000/group/1`  
  
**Key Features of This Code**
1. Efficiency:  
- Combines an optimized search algorithm with caching to reduce the need for redundant group creation.
2. Non-Blocking Behavior:  
- Offloads heavy operations (e.g., database writes) to a background worker using Redis queues.  
3. Responsiveness:  
- Ensures the main application thread doesn’t become unresponsive while creating a group.
