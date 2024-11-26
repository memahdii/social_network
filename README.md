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
  
**Matching Algorithm**  
A simple loop through existing groups checks if there’s a partial match between attributes.  
New groups are created if no suitable group is found.  

**Testing Steps**
1. Install dependencies
2. Run Flask Application by typing ' **flask run** ' in terminal
3. Test API Endpoints:
You can use a tool like Postman or curl to interact with the endpoints
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

**Limitations of this implementation**
1. Efficiency:
   - The matching algorithm iterates over all groups, which is inefficient for large datasets.  
   - No caching leads to repeated database queries for frequent requests.  
3. Scalability:
   - The system might struggle to handle concurrent requests as it directly queries the database.
  
**Later imporvments:**  
- Use queueing, and caching mechanisms to improve app performance.  
