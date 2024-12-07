**Problem Statement**  
- Build a social network app where users join by specifying attributes and group them with others based on attribute similarity.  
Every user should have a unique ID assigned to them once they join.  
After joining users are able to see all the users they have been grouped with  

**API Requirements**  
- Sign-Up API: Accepts user attributes, assigns a unique ID, and groups the user.  
- Sign-In API: Authenticates users via user_id and generates tokens for future requests.  
- Get Group API: Allows users to see group members by providing their ID.  


# Explanation of Code  

Algorithm used for group matching is **Hashing**  
set intersection:  
- First I convert the data to set to hash each attribute  
- Then performing an intersection (set1 & set2)  
- Python computes the hash of each element in one set and checks for its existence in the hash table of the other set.  
- This makes the comparison highly efficient, as each membership check is O(1).  

set1 = {"attr1", "attr2"}  
set2 = {"attr1", "attr5"}  

Hash of "attr1" exists in both sets, so it’s included in the intersection.
intersection = set1 & set2  
print(intersection)  # Output: {"attr1"}  

**Caching Mechanism**  
- Caching is implemented using the flask_caching library and backed by Redis.  
Purpose:  
- Caching helps store frequently accessed data temporarily, reducing database queries and speeding up responses for repeated requests.
  
For instance:  
1. Caching Database Queries: The find_matching_group function uses caching to store the list of groups fetched from the database  
2. Caching HTTP Responses: The /group/<int:user_id> route caches the response for 60 seconds using the @cache.cached decorator:
If the same request is made again within this time, the cached response is returned instead of querying the database.  

**Task Queueing**  
In order to allow the program to handle time-intensive operations asynchronously, and ensuring the app remains responsive while processing tasks in the background, I implemented Tsk Queueing using the rq library and backed by Redis.  

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
- /user/<user_id>:
  - PUT method: Update the user's attributes in the database
  - DELETE method: Remove user from database
  


**Testing Steps**
1. Install the packages using this command `pip install -r requirements.txt` 
2. run Redis using this command in terminal `redis-server`
3. open a new terminal and run flask using this command: `flask run`
4. Start a worker process for the queue: `rq worker`  
5. Run the Testing Script: `python test_flask_app.py`  
- Other options: You can use a tool like Postman or curl to interact with the endpoints
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

**Potential Improvement:**  
- The loop could include a timeout or error-checking mechanism to handle cases where the task fails.
