#!/usr/bin/env python3
"""
LandingOS Feature-Specific Testing Suite
Tests the specific features mentioned in the review request
"""

import requests
import json
import sys
import time
from datetime import datetime

class FeatureSpecificTester:
    def __init__(self, base_url="https://moltbot-config-9p3r.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/landingos"
        self.tests_run = 0
        self.tests_passed = 0
        self.simulation_id = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name} - {details}")
        return success

    def run_test(self, name, method, endpoint, expected_status=200, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_base}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return self.log_test(name, False, f"Unsupported method: {method}"), None

            success = response.status_code == expected_status
            if success:
                try:
                    return self.log_test(name, True), response.json()
                except:
                    return self.log_test(name, True), response.text
            else:
                return self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}: {response.text[:200]}"), None

        except Exception as e:
            return self.log_test(name, False, f"Request failed: {str(e)}"), None

    def test_simulation_no_auto_reset(self):
        """Test that simulation does NOT auto-reset after landing - data preserved for export"""
        print("\n🛸 Testing Simulation No Auto-Reset Feature")
        
        # Create simulation
        config = {
            "terrain_type": "lunar",
            "initial_altitude": 100,  # Low altitude for quick landing
            "descent_velocity": 80,   # Fast descent
            "vibration_amplitude": 0.5,
            "noise_level": 0.1,
            "feature_density": 200
        }
        
        success, response = self.run_test(
            "Create Simulation for Landing Test",
            "POST",
            "simulation/create",
            data=config
        )
        
        if not success or not response:
            return False
            
        self.simulation_id = response.get('id')
        print(f"   Created simulation: {self.simulation_id}")
        
        # Step simulation until landing
        landed = False
        steps_taken = 0
        max_steps = 50
        
        while not landed and steps_taken < max_steps:
            success, response = self.run_test(
                f"Step Simulation (attempt {steps_taken + 1})",
                "POST",
                f"simulation/{self.simulation_id}/step",
                params={"steps": 5}
            )
            
            if success and response:
                final_result = response.get('final_result')
                if final_result and final_result.get('status') == 'landed':
                    landed = True
                    print(f"   Simulation landed after {steps_taken + 1} step attempts")
                    break
            steps_taken += 1
        
        if not landed:
            return self.log_test("Simulation Landing", False, "Failed to land within max steps")
        
        # Get simulation state after landing
        success, state = self.run_test(
            "Get State After Landing",
            "GET",
            f"simulation/{self.simulation_id}/state"
        )
        
        if success and state:
            events_history = state.get('events_history', [])
            metrics_history = state.get('metrics_history', [])
            
            if len(events_history) > 0 and len(metrics_history) > 0:
                return self.log_test(
                    "Data Preserved After Landing", 
                    True, 
                    f"Events: {len(events_history)}, Metrics: {len(metrics_history)}"
                )
            else:
                return self.log_test("Data Preserved After Landing", False, "No data found in history")
        
        return False

    def test_export_endpoints_return_data(self):
        """Test that export endpoints return actual data (not blank)"""
        print("\n📤 Testing Export Endpoints Return Data")
        
        if not self.simulation_id:
            return self.log_test("Export Test", False, "No simulation ID available")
        
        # Test events export
        success, events_data = self.run_test(
            "Export Events Endpoint",
            "GET",
            f"export/simulation/{self.simulation_id}/events",
            params={"format": "json"}
        )
        
        if success and events_data:
            # Check if it's actual data, not blank
            if isinstance(events_data, str) and len(events_data.strip()) > 10:
                try:
                    parsed = json.loads(events_data)
                    if parsed and len(str(parsed)) > 50:  # Reasonable data size
                        self.log_test("Events Export Has Data", True, f"Data size: {len(events_data)} chars")
                    else:
                        self.log_test("Events Export Has Data", False, "Data appears to be minimal/empty")
                except:
                    self.log_test("Events Export Has Data", True, f"Raw data size: {len(events_data)} chars")
            else:
                self.log_test("Events Export Has Data", False, "Export appears blank or too small")
        
        # Test trajectory export
        success, traj_data = self.run_test(
            "Export Trajectory Endpoint",
            "GET",
            f"export/simulation/{self.simulation_id}/trajectory",
            params={"format": "json"}
        )
        
        if success and traj_data:
            if isinstance(traj_data, str) and len(traj_data.strip()) > 10:
                try:
                    parsed = json.loads(traj_data)
                    if parsed and len(str(parsed)) > 50:
                        return self.log_test("Trajectory Export Has Data", True, f"Data size: {len(traj_data)} chars")
                    else:
                        return self.log_test("Trajectory Export Has Data", False, "Data appears minimal/empty")
                except:
                    return self.log_test("Trajectory Export Has Data", True, f"Raw data size: {len(traj_data)} chars")
            else:
                return self.log_test("Trajectory Export Has Data", False, "Export appears blank or too small")
        
        return False

    def test_frame_vo_comparison_apis(self):
        """Test Frame-Based VO comparison APIs"""
        print("\n🔄 Testing Frame-Based VO Comparison APIs")
        
        # Create new simulation for comparison testing
        config = {
            "terrain_type": "lunar",
            "initial_altitude": 200,
            "descent_velocity": 50,
            "vibration_amplitude": 0.5,
            "noise_level": 0.1,
            "feature_density": 200
        }
        
        success, response = self.run_test(
            "Create Simulation for Comparison",
            "POST",
            "simulation/create",
            data=config
        )
        
        if not success or not response:
            return False
            
        comp_sim_id = response.get('id')
        
        # Test enable comparison API
        success, response = self.run_test(
            "Enable FVO Comparison",
            "POST",
            f"simulation/{comp_sim_id}/enable-comparison",
            data={"frame_rate": 30, "enable_fvo": True}
        )
        
        if not success:
            return False
        
        # Test step with comparison
        success, response = self.run_test(
            "Step with Comparison",
            "POST",
            f"simulation/{comp_sim_id}/step-comparison",
            params={"steps": 10}
        )
        
        if success and response:
            final_result = response.get('final_result')
            if final_result and 'evo' in final_result and 'fvo' in final_result:
                self.log_test("Step Comparison Returns Both EVO and FVO", True)
            else:
                self.log_test("Step Comparison Returns Both EVO and FVO", False, "Missing EVO or FVO data")
        
        # Test get comparison results
        success, response = self.run_test(
            "Get Comparison Results",
            "GET",
            f"simulation/{comp_sim_id}/comparison"
        )
        
        if success and response:
            comparison = response.get('comparison')
            if comparison and 'event_based_vo' in comparison and 'frame_based_vo' in comparison:
                return self.log_test("Comparison Results Available", True, "Both EVO and FVO metrics found")
            else:
                return self.log_test("Comparison Results Available", False, "Missing comparison data")
        
        return False

    def test_technical_documentation(self):
        """Test technical documentation accessibility"""
        print("\n📚 Testing Technical Documentation")
        
        # Test if technical report is accessible
        try:
            doc_url = f"{self.base_url}/docs/TECHNICAL_REPORT.md"
            response = requests.get(doc_url, timeout=10)
            
            if response.status_code == 200 and len(response.text) > 1000:
                return self.log_test(
                    "Technical Documentation Accessible", 
                    True, 
                    f"Document size: {len(response.text)} chars"
                )
            else:
                return self.log_test(
                    "Technical Documentation Accessible", 
                    False, 
                    f"Status: {response.status_code}, Size: {len(response.text) if response.text else 0}"
                )
        except Exception as e:
            return self.log_test("Technical Documentation Accessible", False, str(e))

    def run_all_feature_tests(self):
        """Run all feature-specific tests"""
        print("🔍 Starting LandingOS Feature-Specific Tests")
        print("=" * 60)
        
        # Test 1: Simulation no auto-reset
        self.test_simulation_no_auto_reset()
        
        # Test 2: Export endpoints return data
        self.test_export_endpoints_return_data()
        
        # Test 3: Frame-Based VO comparison
        self.test_frame_vo_comparison_apis()
        
        # Test 4: Technical documentation
        self.test_technical_documentation()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Feature Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All feature tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} feature tests failed")
            return 1

def main():
    """Main test runner"""
    tester = FeatureSpecificTester()
    return tester.run_all_feature_tests()

if __name__ == "__main__":
    sys.exit(main())