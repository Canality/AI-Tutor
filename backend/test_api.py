"""
测试Mock API
"""

import http.client
import json

def test_api():
    conn = http.client.HTTPConnection("localhost", 8001)
    
    print("=" * 60)
    print("AI Tutor V3 Mock API Test")
    print("=" * 60)
    
    # Test 1: Root
    print("\n[Test 1] GET /")
    conn.request("GET", "/")
    response = conn.getresponse()
    print(f"Status: {response.status}")
    data = json.loads(response.read().decode())
    print(f"Response: {data}")
    
    # Test 2: Health
    print("\n[Test 2] GET /health")
    conn.request("GET", "/health")
    response = conn.getresponse()
    print(f"Status: {response.status}")
    data = json.loads(response.read().decode())
    print(f"Response: {data}")
    
    # Test 3: Get users
    print("\n[Test 3] GET /api/users")
    conn.request("GET", "/api/users")
    response = conn.getresponse()
    print(f"Status: {response.status}")
    data = json.loads(response.read().decode())
    print(f"Users: {len(data)}")
    for u in data:
        print(f"  - {u['username']}: theta={u['theta']}")
    
    # Test 4: Get theta
    print("\n[Test 4] GET /api/cognitive/theta/1")
    conn.request("GET", "/api/cognitive/theta/1")
    response = conn.getresponse()
    print(f"Status: {response.status}")
    data = json.loads(response.read().decode())
    print(f"Response: {json.dumps(data, indent=2)}")
    
    # Test 5: Update mastery
    print("\n[Test 5] POST /api/cognitive/mastery/update")
    payload = json.dumps({
        "user_id": 1,
        "knowledge_point_id": 101,
        "is_correct": True
    })
    headers = {"Content-type": "application/json"}
    conn.request("POST", "/api/cognitive/mastery/update", payload, headers)
    response = conn.getresponse()
    print(f"Status: {response.status}")
    data = json.loads(response.read().decode())
    print(f"Response: {json.dumps(data, indent=2)}")
    
    # Test 6: Calculate actual score
    print("\n[Test 6] POST /api/cognitive/actual-score/calculate")
    payload = json.dumps({
        "is_correct": True,
        "hint_level": 2,
        "time_spent": 60,
        "expected_time": 60
    })
    conn.request("POST", "/api/cognitive/actual-score/calculate", payload, headers)
    response = conn.getresponse()
    print(f"Status: {response.status}")
    data = json.loads(response.read().decode())
    print(f"Response: {json.dumps(data, indent=2)}")
    
    # Test 7: Get difficulty range
    print("\n[Test 7] GET /api/cognitive/difficulty-range/1")
    conn.request("GET", "/api/cognitive/difficulty-range/1")
    response = conn.getresponse()
    print(f"Status: {response.status}")
    data = json.loads(response.read().decode())
    print(f"Response: {json.dumps(data, indent=2)}")
    
    # Test 8: Get report
    print("\n[Test 8] GET /api/cognitive/report/1")
    conn.request("GET", "/api/cognitive/report/1")
    response = conn.getresponse()
    print(f"Status: {response.status}")
    data = json.loads(response.read().decode())
    print(f"Response: {json.dumps(data, indent=2)}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("All API tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_api()
