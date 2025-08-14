import requests
import sys
import json
from datetime import datetime
import time

class AvatarProductivityAPITester:
    def __init__(self, base_url="https://taskavatar.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.task_ids = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - {name}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test API health check"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/",
            200
        )
        return success

    def test_create_user(self):
        """Test user creation"""
        user_data = {
            "name": f"Test User {datetime.now().strftime('%H%M%S')}",
            "email": f"test{datetime.now().strftime('%H%M%S')}@example.com"
        }
        
        success, response = self.run_test(
            "Create User",
            "POST",
            "api/users",
            200,
            data=user_data
        )
        
        if success and 'id' in response:
            self.user_id = response['id']
            print(f"   Created user with ID: {self.user_id}")
            return True
        return False

    def test_get_user(self):
        """Test getting user by ID"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
            
        success, response = self.run_test(
            "Get User",
            "GET",
            f"api/users/{self.user_id}",
            200
        )
        
        if success:
            expected_fields = ['id', 'name', 'email', 'xp', 'level', 'avatar_mood']
            for field in expected_fields:
                if field not in response:
                    print(f"❌ Missing field in user response: {field}")
                    return False
            print(f"   User XP: {response.get('xp', 0)}, Level: {response.get('level', 1)}")
            return True
        return False

    def test_create_task(self):
        """Test task creation"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
            
        task_data = {
            "title": "Test Task - Complete Project",
            "description": "This is a test task for the avatar productivity app",
            "xp_reward": 25
        }
        
        success, response = self.run_test(
            "Create Task",
            "POST",
            "api/tasks",
            200,
            data=task_data,
            params={"user_id": self.user_id}
        )
        
        if success and 'id' in response:
            task_id = response['id']
            self.task_ids.append(task_id)
            print(f"   Created task with ID: {task_id}")
            return True
        return False

    def test_get_user_tasks(self):
        """Test getting user tasks"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
            
        success, response = self.run_test(
            "Get User Tasks",
            "GET",
            f"api/tasks/{self.user_id}",
            200
        )
        
        if success:
            if isinstance(response, list):
                print(f"   Found {len(response)} tasks for user")
                if len(response) > 0:
                    task = response[0]
                    expected_fields = ['id', 'user_id', 'title', 'completed', 'xp_reward']
                    for field in expected_fields:
                        if field not in task:
                            print(f"❌ Missing field in task response: {field}")
                            return False
                return True
            else:
                print("❌ Expected list of tasks")
                return False
        return False

    def test_complete_task(self):
        """Test task completion with AI coaching"""
        if not self.task_ids:
            print("❌ No task ID available for testing")
            return False
            
        task_id = self.task_ids[0]
        
        success, response = self.run_test(
            "Complete Task",
            "POST",
            "api/tasks/complete",
            200,
            data={"task_id": task_id}
        )
        
        if success:
            expected_fields = ['message', 'xp_gained', 'new_xp', 'new_level', 'level_up', 'avatar_mood', 'ai_message']
            for field in expected_fields:
                if field not in response:
                    print(f"❌ Missing field in completion response: {field}")
                    return False
            
            print(f"   XP Gained: {response.get('xp_gained', 0)}")
            print(f"   New XP: {response.get('new_xp', 0)}")
            print(f"   New Level: {response.get('new_level', 1)}")
            print(f"   Level Up: {response.get('level_up', False)}")
            print(f"   Avatar Mood: {response.get('avatar_mood', 'neutral')}")
            print(f"   AI Message: {response.get('ai_message', 'No message')[:100]}...")
            
            # Wait a moment for AI processing
            time.sleep(2)
            return True
        return False

    def test_get_avatar_state(self):
        """Test getting avatar state"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
            
        success, response = self.run_test(
            "Get Avatar State",
            "GET",
            f"api/avatar-state/{self.user_id}",
            200
        )
        
        if success:
            expected_fields = ['mood', 'animation', 'message', 'xp', 'level']
            for field in expected_fields:
                if field not in response:
                    print(f"❌ Missing field in avatar state response: {field}")
                    return False
            
            print(f"   Avatar Mood: {response.get('mood', 'neutral')}")
            print(f"   Animation: {response.get('animation', 'idle')}")
            print(f"   Message: {response.get('message', 'No message')[:100]}...")
            return True
        return False

    def test_delete_task(self):
        """Test task deletion"""
        if not self.task_ids:
            print("❌ No task ID available for testing")
            return False
            
        # Create a new task to delete
        task_data = {
            "title": "Task to Delete",
            "description": "This task will be deleted",
            "xp_reward": 10
        }
        
        success, response = self.run_test(
            "Create Task for Deletion",
            "POST",
            "api/tasks",
            200,
            data=task_data,
            params={"user_id": self.user_id}
        )
        
        if not success or 'id' not in response:
            return False
            
        delete_task_id = response['id']
        
        success, response = self.run_test(
            "Delete Task",
            "DELETE",
            f"api/tasks/{delete_task_id}",
            200
        )
        
        return success

    def test_error_cases(self):
        """Test error handling"""
        print("\n🔍 Testing Error Cases...")
        
        # Test getting non-existent user
        success, _ = self.run_test(
            "Get Non-existent User",
            "GET",
            "api/users/non-existent-id",
            404
        )
        
        if not success:
            return False
        
        # Test completing non-existent task
        success, _ = self.run_test(
            "Complete Non-existent Task",
            "POST",
            "api/tasks/complete",
            404,
            data={"task_id": "non-existent-task-id"}
        )
        
        if not success:
            return False
            
        # Test deleting non-existent task
        success, _ = self.run_test(
            "Delete Non-existent Task",
            "DELETE",
            "api/tasks/non-existent-task-id",
            404
        )
        
        return success

def main():
    print("🚀 Starting Avatar Productivity API Tests")
    print("=" * 50)
    
    tester = AvatarProductivityAPITester()
    
    # Run all tests in sequence
    test_results = []
    
    test_results.append(tester.test_health_check())
    test_results.append(tester.test_create_user())
    test_results.append(tester.test_get_user())
    test_results.append(tester.test_create_task())
    test_results.append(tester.test_get_user_tasks())
    test_results.append(tester.test_complete_task())
    test_results.append(tester.test_get_avatar_state())
    test_results.append(tester.test_delete_task())
    test_results.append(tester.test_error_cases())
    
    # Print final results
    print("\n" + "=" * 50)
    print("📊 FINAL TEST RESULTS")
    print("=" * 50)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Backend API is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the backend implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())