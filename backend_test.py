import requests
import sys
import json
from datetime import datetime

class DublinStudyAPITester:
    def __init__(self, base_url="https://dublin-study.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.admin_token = None
        self.school_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.user_id = None
        self.enrollment_id = None
        self.school_id = None
        self.course_id = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f" (Expected: {expected_status})"
                try:
                    error_data = response.json()
                    details += f" - {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f" - {response.text[:100]}"

            self.log_test(name, success, details)
            
            if success:
                try:
                    return response.json()
                except:
                    return {}
            return None

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return None

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API", "GET", "", 200)

    def test_seed_database(self):
        """Seed the database with test data"""
        result = self.run_test("Seed Database", "POST", "seed", 200)
        if result:
            print(f"   Seeded: {result.get('schools', 0)} schools, {result.get('courses', 0)} courses")
        return result

    def test_user_registration(self):
        """Test user registration"""
        test_user = {
            "name": f"Test User {datetime.now().strftime('%H%M%S')}",
            "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
            "password": "TestPass123!"
        }
        
        result = self.run_test("User Registration", "POST", "auth/register", 200, test_user)
        if result and 'access_token' in result:
            self.token = result['access_token']
            self.user_id = result['user']['id']
            print(f"   Registered user: {result['user']['name']}")
            return True
        return False

    def test_user_login(self):
        """Test user login with existing credentials"""
        if not self.user_id:
            return False
            
        # Create a new user for login test
        login_user = {
            "name": "Login Test User",
            "email": f"login_{datetime.now().strftime('%H%M%S')}@example.com",
            "password": "LoginPass123!"
        }
        
        # Register first
        reg_result = self.run_test("Register for Login Test", "POST", "auth/register", 200, login_user)
        if not reg_result:
            return False
            
        # Now test login
        login_data = {
            "email": login_user["email"],
            "password": login_user["password"]
        }
        
        result = self.run_test("User Login", "POST", "auth/login", 200, login_data)
        if result and 'access_token' in result:
            print(f"   Logged in user: {result['user']['name']}")
            return True
        return False

    def test_get_user_profile(self):
        """Test getting current user profile"""
        if not self.token:
            self.log_test("Get User Profile", False, "No auth token")
            return False
            
        result = self.run_test("Get User Profile", "GET", "auth/me", 200)
        if result:
            print(f"   Profile: {result.get('name', 'Unknown')}")
            return True
        return False

    def test_get_schools(self):
        """Test getting all schools"""
        result = self.run_test("Get Schools", "GET", "schools", 200)
        if result and isinstance(result, list):
            print(f"   Found {len(result)} schools")
            return result
        return None

    def test_get_school_detail(self, school_id="school-1"):
        """Test getting school details"""
        result = self.run_test("Get School Detail", "GET", f"schools/{school_id}", 200)
        if result:
            print(f"   School: {result.get('name', 'Unknown')}")
            return result
        return None

    def test_get_school_courses(self, school_id="school-1"):
        """Test getting courses for a school"""
        result = self.run_test("Get School Courses", "GET", f"schools/{school_id}/courses", 200)
        if result and isinstance(result, list):
            print(f"   Found {len(result)} courses for school")
            return result
        return None

    def test_get_all_courses(self):
        """Test getting all courses"""
        result = self.run_test("Get All Courses", "GET", "courses", 200)
        if result and isinstance(result, list):
            print(f"   Found {len(result)} total courses")
            return result
        return None

    def test_get_course_detail(self, course_id="course-1"):
        """Test getting course details"""
        result = self.run_test("Get Course Detail", "GET", f"courses/{course_id}", 200)
        if result:
            print(f"   Course: {result.get('name', 'Unknown')}")
            return result
        return None

    def test_create_enrollment(self, course_id="course-1"):
        """Test creating an enrollment"""
        if not self.token:
            self.log_test("Create Enrollment", False, "No auth token")
            return False
            
        start_date = "2025-02-10"
        result = self.run_test(
            "Create Enrollment", 
            "POST", 
            f"enrollments?course_id={course_id}&start_date={start_date}", 
            200
        )
        if result:
            self.enrollment_id = result.get('id')
            print(f"   Enrollment ID: {self.enrollment_id}")
            return True
        return False

    def test_get_user_enrollments(self):
        """Test getting user enrollments"""
        if not self.token:
            self.log_test("Get User Enrollments", False, "No auth token")
            return False
            
        result = self.run_test("Get User Enrollments", "GET", "enrollments", 200)
        if result and isinstance(result, list):
            print(f"   Found {len(result)} enrollments")
            return result
        return None

    def test_get_enrollment_detail(self):
        """Test getting enrollment details"""
        if not self.token or not self.enrollment_id:
            self.log_test("Get Enrollment Detail", False, "No auth token or enrollment ID")
            return False
            
        result = self.run_test("Get Enrollment Detail", "GET", f"enrollments/{self.enrollment_id}", 200)
        if result:
            print(f"   Enrollment: {result.get('course_name', 'Unknown')}")
            return True
        return False

    def test_create_checkout_session(self):
        """Test creating Stripe checkout session"""
        if not self.token or not self.enrollment_id:
            self.log_test("Create Checkout Session", False, "No auth token or enrollment ID")
            return False
            
        checkout_data = {
            "enrollment_id": self.enrollment_id,
            "origin_url": "https://dublin-study.preview.emergentagent.com"
        }
        
        result = self.run_test("Create Checkout Session", "POST", "payments/checkout", 200, checkout_data)
        if result and 'url' in result:
            print(f"   Checkout URL created: {result['url'][:50]}...")
            return result
        return None

    def test_transport_routes(self):
        """Test getting transport routes"""
        result = self.run_test("Get Transport Routes", "GET", "transport/routes", 200)
        if result and isinstance(result, list):
            print(f"   Found {len(result)} transport routes")
            return result
        return None

    def test_government_agencies(self):
        """Test getting government agencies"""
        result = self.run_test("Get Government Agencies", "GET", "services/agencies", 200)
        if result and isinstance(result, list):
            print(f"   Found {len(result)} agencies")
            return result
        return None

    def test_agencies_by_category(self, category="immigration"):
        """Test getting agencies by category"""
        result = self.run_test("Get Agencies by Category", "GET", f"services/agencies/{category}", 200)
        if result and isinstance(result, list):
            print(f"   Found {len(result)} {category} agencies")
            return result
        return None

    def test_pps_guide(self):
        """Test PPS guide endpoint"""
        result = self.run_test("Get PPS Guide", "GET", "guides/pps", 200)
        if result and 'title' in result:
            print(f"   Guide: {result.get('title', 'Unknown')}")
            return True
        return False

    def test_gnib_guide(self):
        """Test GNIB guide endpoint"""
        result = self.run_test("Get GNIB Guide", "GET", "guides/gnib", 200)
        if result and 'title' in result:
            print(f"   Guide: {result.get('title', 'Unknown')}")
            return True
        return False

    def test_passport_guide(self):
        """Test passport guide endpoint"""
        result = self.run_test("Get Passport Guide", "GET", "guides/passport", 200)
        if result and 'title' in result:
            print(f"   Guide: {result.get('title', 'Unknown')}")
            return True
        return False

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Dublin Study API Tests")
        print("=" * 50)
        
        # Basic API tests
        self.test_root_endpoint()
        self.test_seed_database()
        
        # Authentication tests
        self.test_user_registration()
        self.test_user_login()
        self.test_get_user_profile()
        
        # Schools and courses tests
        schools = self.test_get_schools()
        if schools and len(schools) > 0:
            self.test_get_school_detail(schools[0]['id'])
            self.test_get_school_courses(schools[0]['id'])
        
        courses = self.test_get_all_courses()
        if courses and len(courses) > 0:
            self.test_get_course_detail(courses[0]['id'])
            
            # Enrollment tests (requires auth)
            if self.token:
                self.test_create_enrollment(courses[0]['id'])
                self.test_get_user_enrollments()
                self.test_get_enrollment_detail()
                self.test_create_checkout_session()
        
        # Transport and services tests
        self.test_transport_routes()
        self.test_government_agencies()
        self.test_agencies_by_category("immigration")
        
        # Guides tests
        self.test_pps_guide()
        self.test_gnib_guide()
        self.test_passport_guide()
        
        # Print results
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"❌ {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = DublinStudyAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())