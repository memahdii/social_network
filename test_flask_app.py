import requests
import time

BASE_URL = "http://localhost:5000"


def test_signup():
    data = {"attributes": ["attr1", "attr2"]}
    start = time.time()
    response = requests.post(f"{BASE_URL}/signup", json=data)
    duration = time.time() - start
    print("Signup Response:", response.json(), f"Time: {duration:.3f}s")


def test_signin(user_id):
    data = {"user_id": user_id}
    start = time.time()
    response = requests.post(f"{BASE_URL}/signin", json=data)
    duration = time.time() - start
    print("Signin Response:", response.json(), f"Time: {duration:.3f}s")


def test_get_group(user_id):
    start = time.time()
    response = requests.get(f"{BASE_URL}/group/{user_id}")
    duration = time.time() - start
    print("Get Group Response:", response.json(), f"Time: {duration:.3f}s")


def test_flow():
    print("=== Running Signup Test ===")
    test_signup()
    
    print("\n=== Running Signin Test ===")
    test_signin(1)  # Assuming the user created has ID = 1

    print("\n=== Running Get Group Test ===")
    test_get_group(1)

    print("\n=== Running Update User Attribute Test ===")
    test_update_user(35)

    print("\n=== Running Delete User Test ===")
    test_delete_user(35)

if __name__ == "__main__":
    test_flow()
