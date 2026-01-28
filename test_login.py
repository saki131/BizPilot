import httpx

# テスト用のログインリクエスト
url = "http://localhost:8002/api/auth/login"
data = {
    "username": "admin",
    "password": "password123"
}

try:
    with httpx.Client() as client:
        response = client.post(url, data=data)
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {response.json()}")
        except:
            print(f"Response Text: {response.text}")
except Exception as e:
    print(f"Error: {e}")