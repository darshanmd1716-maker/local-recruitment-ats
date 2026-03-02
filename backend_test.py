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

    def test_check_duplicate(self):
        """Test duplicate candidate detection"""
        # Test with email and mobile
        success1, response1 = self.run_test(
            "Check Duplicate - Email", 
            "GET", 
            "check-duplicate?email=john.doe@example.com", 
            200
        )
        
        success2, response2 = self.run_test(
            "Check Duplicate - Mobile", 
            "GET", 
            "check-duplicate?mobile=+1-555-0123", 
            200
        )
        
        # Test with non-existent contact
        success3, response3 = self.run_test(
            "Check Duplicate - Non-existent", 
            "GET", 
            "check-duplicate?email=nonexistent@example.com", 
            200
        )
        
        if success1 and success2 and success3:
            # Check response structure
            if 'is_duplicate' not in response1:
                print("❌ Missing 'is_duplicate' field in response")
                return False
            print(f"   Email duplicate check: {response1.get('is_duplicate')}")
            print(f"   Mobile duplicate check: {response2.get('is_duplicate')}")
            print(f"   Non-existent duplicate check: {response3.get('is_duplicate')}")
        
        return success1 and success2 and success3

    def test_get_duplicates_for_job(self):
        """Test getting duplicates for a specific job"""
        if not self.job_id:
            print("❌ No job ID available for duplicates test")
            return False
        
        success, response = self.run_test(
            f"Get Duplicates for Job {self.job_id}", 
            "GET", 
            f"duplicates/{self.job_id}", 
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} duplicate candidates")
        
        return success

    def test_compare_candidates(self):
        """Test comparing candidates"""
        if not self.job_id:
            print("❌ No job ID available for comparison")
            return False
        
        # First get candidates to compare
        success, candidates = self.run_test("Get Candidates for Comparison", "GET", f"candidates/{self.job_id}", 200)
        if not success or not candidates or len(candidates) == 0:
            print("❌ No candidates available for comparison test")
            return False
        
        # Create another dummy candidate if we only have one
        if len(candidates) == 1:
            dummy_resume_content2 = """
            Jane Smith
            Senior Full Stack Developer
            
            Email: jane.smith@example.com
            Phone: +1-555-0124
            
            Experience: 8 years
            
            Skills:
            - Python, React, Node.js
            - AWS, Kubernetes
            - MongoDB, PostgreSQL
            - Git, Docker
            
            Current Role: Lead Developer at WebCorp
            """
            
            files = {
                'files': ('jane_smith_resume.txt', dummy_resume_content2.encode(), 'text/plain')
            }
            
            success, _ = self.run_test(
                "Add Second Candidate for Comparison", 
                "POST", 
                f"process-resumes/{self.job_id}", 
                200, 
                files=files
            )
            
            if not success:
                print("❌ Failed to add second candidate")
                return False
            
            # Re-fetch candidates
            success, candidates = self.run_test("Re-fetch Candidates", "GET", f"candidates/{self.job_id}", 200)
            if not success or len(candidates) < 2:
                print("❌ Still don't have enough candidates for comparison")
                return False
        
        # Test comparison with 2 candidates
        candidate_ids = [candidates[0]['id'], candidates[1]['id']]
        comparison_data = {
            "candidate_ids": candidate_ids
        }
        
        success, response = self.run_test(
            "Compare 2 Candidates", 
            "POST", 
            "compare-candidates", 
            200, 
            comparison_data
        )
        
        if success and isinstance(response, dict):
            required_fields = ['candidates', 'comparison_metrics']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing field in comparison result: {field}")
                    return False
            
            print(f"   Compared {len(response['candidates'])} candidates")
            metrics = response['comparison_metrics']
            print(f"   Common skills: {metrics.get('common_skills_count', 0)}")
            print(f"   Total unique skills: {metrics.get('total_unique_skills', 0)}")
        
        # Test error case - too few candidates
        success_err1, _ = self.run_test(
            "Compare - Too Few Candidates", 
            "POST", 
            "compare-candidates", 
            400, 
            {"candidate_ids": [candidate_ids[0]]}
        )
        
        # Test error case - too many candidates (simulate with repeated IDs)
        too_many_ids = candidate_ids * 3  # 6 candidates (over limit of 5)
        success_err2, _ = self.run_test(
            "Compare - Too Many Candidates", 
            "POST", 
            "compare-candidates", 
            400, 
            {"candidate_ids": too_many_ids}
        )
        
        return success and success_err1 and success_err2

    def test_process_resumes_with_duplicates(self):
        """Test resume processing that includes duplicate detection"""
        if not self.job_id:
            print("❌ No job ID available for duplicate processing test")
            return False

        # Process the same resume again to trigger duplicate detection
        duplicate_resume_content = """
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
        
        files = {
            'files': ('john_doe_duplicate_resume.txt', duplicate_resume_content.encode(), 'text/plain')
        }
        
        success, response = self.run_test(
            "Process Duplicate Resume", 
            "POST", 
            f"process-resumes/{self.job_id}", 
            200, 
            files=files
        )
        
        if success and isinstance(response, dict):
            # Check if duplicates_found field exists and has data
            if 'duplicates_found' not in response:
                print("❌ Missing 'duplicates_found' field in processing result")
                return False
            
            duplicates = response['duplicates_found']
            print(f"   Found {len(duplicates)} duplicates in processing")
            
            if len(duplicates) > 0:
                duplicate = duplicates[0]
                required_dup_fields = ['new_name', 'existing_name', 'match_type', 'existing_job']
                for field in required_dup_fields:
                    if field not in duplicate:
                        print(f"❌ Missing field in duplicate info: {field}")
                        return False
                        
                print(f"   Duplicate match type: {duplicate.get('match_type')}")
                print(f"   Existing candidate: {duplicate.get('existing_name')}")
        
        return success

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