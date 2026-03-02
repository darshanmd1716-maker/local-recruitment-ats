import requests
import sys
import json
import tempfile
import os
from datetime import datetime
from io import BytesIO

class ATSAPITester:
    def __init__(self, base_url="https://local-ats-agent.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.job_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, response_type='json'):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=headers)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                headers['Content-Type'] = 'application/json'
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response_type == 'json':
                    try:
                        return success, response.json()
                    except:
                        return success, {}
                else:
                    return success, response.content
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.text:
                    print(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic health endpoint"""
        return self.run_test("Health Check", "GET", "health", 200)

    def test_get_stats(self):
        """Test getting stats"""
        success, response = self.run_test("Get Stats", "GET", "stats", 200)
        if success and isinstance(response, dict):
            required_fields = ['total_jobs', 'total_candidates', 'shortlisted', 'hold', 'rejected_future']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing field in stats: {field}")
                    return False
        return success

    def test_create_job(self):
        """Test creating a job description"""
        job_data = {
            "title": "Senior Python Developer",
            "raw_text": """
            We are looking for a Senior Python Developer with 5+ years of experience.
            
            Required Skills:
            - Python, Django, Flask
            - AWS, Docker, Kubernetes
            - REST APIs, PostgreSQL
            - Git, CI/CD
            
            Experience: 5-8 years
            Location: Remote/Hybrid
            """
        }
        
        success, response = self.run_test("Create Job", "POST", "jobs", 200, job_data)
        if success and 'id' in response:
            self.job_id = response['id']
            print(f"   Created job ID: {self.job_id}")
        return success

    def test_get_jobs(self):
        """Test getting all jobs"""
        success, response = self.run_test("Get Jobs", "GET", "jobs", 200)
        if success and isinstance(response, list) and len(response) > 0:
            job = response[0]
            required_fields = ['id', 'title', 'raw_text', 'required_skills']
            for field in required_fields:
                if field not in job:
                    print(f"❌ Missing field in job: {field}")
                    return False
        return success

    def test_get_specific_job(self):
        """Test getting a specific job"""
        if not self.job_id:
            print("❌ No job ID available for testing")
            return False
        
        return self.run_test(f"Get Job {self.job_id}", "GET", f"jobs/{self.job_id}", 200)[0]

    def test_process_resumes(self):
        """Test processing resumes"""
        if not self.job_id:
            print("❌ No job ID available for processing")
            return False

        # Create a dummy PDF file content
        dummy_resume_content = """
        John Doe
        Senior Software Engineer
        
        Email: john.doe@example.com
        Phone: +1-555-0123
        
        Experience: 6 years
        
        Skills:
        - Python, Django, Flask
        - AWS, Docker
        - PostgreSQL, Redis
        - Git, Jenkins
        
        Current Role: Senior Python Developer at TechCorp
        """
        
        # Create a temporary file
        files = {
            'files': ('john_doe_resume.txt', dummy_resume_content.encode(), 'text/plain')
        }
        
        success, response = self.run_test(
            "Process Resumes", 
            "POST", 
            f"process-resumes/{self.job_id}", 
            200, 
            files=files
        )
        
        if success and isinstance(response, dict):
            required_fields = ['job_id', 'total_processed', 'shortlisted', 'hold', 'rejected_future', 'top_candidates']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing field in processing result: {field}")
                    return False
        return success

    def test_get_candidates(self):
        """Test getting candidates for a job"""
        if not self.job_id:
            print("❌ No job ID available for getting candidates")
            return False
            
        success, response = self.run_test(f"Get Candidates for Job", "GET", f"candidates/{self.job_id}", 200)
        if success and isinstance(response, list) and len(response) > 0:
            candidate = response[0]
            required_fields = ['id', 'job_id', 'name', 'match_percentage', 'category']
            for field in required_fields:
                if field not in candidate:
                    print(f"❌ Missing field in candidate: {field}")
                    return False
        return success

    def test_update_candidate(self):
        """Test updating candidate details"""
        if not self.job_id:
            print("❌ No job ID available for updating candidate")
            return False
        
        # First get candidates to get a candidate ID
        success, candidates = self.run_test("Get Candidates for Update", "GET", f"candidates/{self.job_id}", 200)
        if not success or not candidates or len(candidates) == 0:
            print("❌ No candidates available for update test")
            return False
        
        candidate_id = candidates[0]['id']
        update_data = {
            "current_ctc": "12 LPA",
            "expected_ctc": "15 LPA", 
            "notice_period": "30 days",
            "negotiable": "Yes",
            "candidate_response": "Yes",
            "remarks": "Good candidate for the role"
        }
        
        return self.run_test(
            f"Update Candidate {candidate_id}", 
            "PUT", 
            f"candidates/{candidate_id}", 
            200, 
            update_data
        )[0]

    def test_export_excel(self):
        """Test Excel export"""
        if not self.job_id:
            print("❌ No job ID available for export")
            return False
        
        success, content = self.run_test(
            "Export Excel", 
            "GET", 
            f"export/{self.job_id}", 
            200,
            response_type='binary'
        )
        
        if success and content:
            print(f"   Excel file size: {len(content)} bytes")
        return success

    def test_filter_candidates_by_category(self):
        """Test filtering candidates by category"""
        if not self.job_id:
            print("❌ No job ID available for filtering")
            return False
        
        categories = ['Shortlisted', 'Hold', 'Rejected_Future']
        for category in categories:
            success, response = self.run_test(
                f"Filter Candidates - {category}", 
                "GET", 
                f"candidates/{self.job_id}?category={category}", 
                200
            )
            if not success:
                return False
        return True

    def test_delete_candidate(self):
        """Test deleting a candidate"""
        if not self.job_id:
            print("❌ No job ID available for delete test")
            return False
        
        # First get candidates to get a candidate ID
        success, candidates = self.run_test("Get Candidates for Delete", "GET", f"candidates/{self.job_id}", 200)
        if not success or not candidates or len(candidates) == 0:
            print("❌ No candidates available for delete test")
            return False
        
        candidate_id = candidates[0]['id']
        return self.run_test(
            f"Delete Candidate {candidate_id}", 
            "DELETE", 
            f"candidates/{candidate_id}", 
            200
        )[0]

    def test_delete_job(self):
        """Test deleting a job"""
        if not self.job_id:
            print("❌ No job ID available for delete")
            return False
        
        return self.run_test(f"Delete Job {self.job_id}", "DELETE", f"jobs/{self.job_id}", 200)[0]

def main():
    print("🚀 Starting ATS API Tests...")
    print("=" * 50)
    
    tester = ATSAPITester()
    
    # Test sequence
    tests = [
        ("Health Check", tester.test_health_check),
        ("Get Initial Stats", tester.test_get_stats),
        ("Create Job", tester.test_create_job),
        ("Get All Jobs", tester.test_get_jobs),
        ("Get Specific Job", tester.test_get_specific_job),
        ("Process Resumes", tester.test_process_resumes),
        ("Get Candidates", tester.test_get_candidates),
        ("Update Candidate", tester.test_update_candidate),
        ("Export Excel", tester.test_export_excel),
        ("Filter Candidates by Category", tester.test_filter_candidates_by_category),
        ("Delete Candidate", tester.test_delete_candidate),
        ("Delete Job", tester.test_delete_job),
        ("Get Final Stats", tester.test_get_stats),
    ]
    
    failed_tests = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            if not result:
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed_tests.append(test_name)
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if failed_tests:
        print(f"\n❌ Failed Tests ({len(failed_tests)}):")
        for test in failed_tests:
            print(f"   - {test}")
    else:
        print("\n✅ All tests passed!")
    
    print(f"\n⏱️  Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())