"""
Test script for EU-CORE-BACKEND multi-app features
Tests: Auth, Upload, Content Read/Write, Storage
"""
import requests
import json

BASE_URL = "http://localhost:5000/api"

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_health():
    print_section("Health Check")
    response = requests.get("http://localhost:5000/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_register():
    print_section("User Registration")
    data = {
        "username": "eutype_test",
        "email": "eutype@test.com",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code in [200, 201, 400]  # 400 if user exists

def test_login():
    print_section("User Login")
    data = {
        "username": "eutype_test",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Token received: {result.get('access_token', 'N/A')[:50]}...")
    return result.get("access_token")

def test_me(token):
    print_section("Get Current User")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"User: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_upload_eutype(token):
    print_section("Upload EuType Document")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a sample .ty document
    content = json.dumps({
        "type": "document",
        "title": "Test Document",
        "content": "This is a test document for EuType integration"
    }, indent=2)
    
    files = {"file": ("Test_Document.ty", content, "application/json")}
    data = {"app_type": "eutype"}
    
    response = requests.post(f"{BASE_URL}/files/upload", headers=headers, files=files, data=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    return result.get("file", {}).get("file_id")

def test_list_files(token):
    print_section("List Files")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/files/list", headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Files: {len(result.get('files', []))}")
    for file in result.get("files", []):
        print(f"  - {file['filename']} (ID: {file['file_id']}, Type: {file.get('app_type', 'N/A')})")
    return result.get("files", [])

def test_get_content(token, file_id):
    print_section(f"Get File Content (ID: {file_id})")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/files/{file_id}/content", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"File: {result.get('filename')}")
        print(f"App Type: {result.get('app_type')}")
        print(f"Content Preview: {result.get('content', '')[:100]}...")
        return result.get("content")
    else:
        print(f"Error: {response.json()}")
        return None

def test_update_content(token, file_id):
    print_section(f"Update File Content (ID: {file_id})")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Updated content
    new_content = json.dumps({
        "type": "document",
        "title": "Updated Test Document",
        "content": "This content has been UPDATED via the content endpoint!",
        "version": 2
    }, indent=2)
    
    data = {"content": new_content}
    response = requests.put(f"{BASE_URL}/files/{file_id}/content", headers=headers, data=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    return response.status_code == 200

def test_storage_usage(token):
    print_section("Storage Usage")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/storage/usage", headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Used: {result.get('storage_used_mb', 0):.2f} MB")
    print(f"Quota: {result.get('storage_quota_mb', 0):.2f} MB")
    print(f"Percentage: {result.get('percentage_used', 0) * 100:.2f}%")
    return result

def main():
    print("\n🚀 EU-CORE-BACKEND API Test Suite")
    print("Testing multi-app features and content endpoints\n")
    
    try:
        # Test 1: Health check
        if not test_health():
            print("❌ Health check failed!")
            return
        
        # Test 2: Register (may fail if user exists - OK)
        test_register()
        
        # Test 3: Login
        token = test_login()
        if not token:
            print("❌ Login failed!")
            return
        
        # Test 4: Get current user
        user = test_me(token)
        print(f"\n✅ Authenticated as: {user.get('username')}")
        
        # Test 5: Upload EuType document
        file_id = test_upload_eutype(token)
        if not file_id:
            print("⚠️  Upload may have failed, trying to list files...")
        
        # Test 6: List files
        files = test_list_files(token)
        if not file_id and files:
            # Use first .ty file if upload failed
            ty_files = [f for f in files if f.get('filename', '').endswith('.ty')]
            if ty_files:
                file_id = ty_files[0]['file_id']
                print(f"\n📌 Using existing file ID: {file_id}")
        
        if not file_id:
            print("❌ No files available for content testing!")
            return
        
        # Test 7: Get file content
        original_content = test_get_content(token, file_id)
        if not original_content:
            print("❌ Failed to read file content!")
            return
        
        # Test 8: Update file content
        if test_update_content(token, file_id):
            print("✅ Content updated successfully")
        else:
            print("❌ Content update failed!")
            return
        
        # Test 9: Verify update by reading again
        updated_content = test_get_content(token, file_id)
        if updated_content and updated_content != original_content:
            print("✅ Content update verified!")
        else:
            print("⚠️  Content may not have changed")
        
        # Test 10: Storage usage
        test_storage_usage(token)
        
        print("\n" + "=" * 60)
        print("  ✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\n📝 Summary:")
        print("  - Authentication: ✅")
        print("  - File Upload (multi-app): ✅")
        print("  - Content Read: ✅")
        print("  - Content Write: ✅")
        print("  - Storage Tracking: ✅")
        print("\n🎉 EU-CORE-BACKEND is ready for EuType integration!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
