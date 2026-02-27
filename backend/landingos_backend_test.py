import requests
import sys
import time
from datetime import datetime

class LandingOSAPITester:
    def __init__(self, base_url="https://links-1.preview.emergentagent.com/api/landingos"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failed_tests = []
        self.simulation_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=15)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                except:
                    print(f"   Response: {response.text[:200]}")
            else:
                self.tests_failed += 1
                self.failed_tests.append(name)
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response: {response.text[:200]}")

            return success, response

        except requests.exceptions.Timeout:
            self.tests_failed += 1
            self.failed_tests.append(name)
            print(f"❌ Failed - Request timeout")
            return False, None
        except requests.exceptions.ConnectionError as e:
            self.tests_failed += 1
            self.failed_tests.append(name)
            print(f"❌ Failed - Connection error: {str(e)}")
            return False, None
        except Exception as e:
            self.tests_failed += 1
            self.failed_tests.append(name)
            print(f"❌ Failed - Error: {str(e)}")
            return False, None

    def test_terrain_types(self):
        """Test terrain types endpoint"""
        success, response = self.run_test(
            "Get Terrain Types",
            "GET",
            "terrain/types",
            200
        )
        if success:
            data = response.json()
            if 'types' in data and len(data['types']) > 0:
                print(f"   ✓ Found {len(data['types'])} terrain types")
                return True
        return False

    def test_terrain_features(self):
        """Test terrain features endpoint"""
        success, response = self.run_test(
            "Get Lunar Terrain Features",
            "GET",
            "terrain/lunar/features",
            200,
            params={"count": 50}
        )
        if success:
            data = response.json()
            if 'features' in data and len(data['features']) > 0:
                print(f"   ✓ Generated {len(data['features'])} terrain features")
                return True
        return False

    def test_ai_status(self):
        """Test AI analysis status"""
        success, response = self.run_test(
            "AI Analysis Status",
            "GET",
            "ai/status",
            200
        )
        if success:
            data = response.json()
            print(f"   AI Enabled: {data.get('enabled', False)}")
            print(f"   Message: {data.get('message', 'No message')}")
            return True
        return False

    def test_simulation_create(self):
        """Test simulation creation"""
        config_data = {
            "terrain_type": "lunar",
            "initial_altitude": 1000.0,
            "descent_velocity": 50.0,
            "vibration_amplitude": 0.5,
            "vibration_frequency": 10.0,
            "noise_level": 0.1,
            "feature_density": 200
        }
        
        success, response = self.run_test(
            "Create Simulation",
            "POST",
            "simulation/create",
            200,
            data=config_data
        )
        
        if success:
            data = response.json()
            if 'id' in data and 'status' in data:
                self.simulation_id = data['id']
                print(f"   ✓ Created simulation with ID: {self.simulation_id}")
                print(f"   Status: {data['status']}")
                print(f"   Initial altitude: {data['altitude']}m")
                return True
        return False

    def test_simulation_step(self):
        """Test simulation stepping"""
        if not self.simulation_id:
            print("   ⚠ No simulation ID available, skipping step test")
            return False
            
        success, response = self.run_test(
            "Step Simulation",
            "POST",
            f"simulation/{self.simulation_id}/step",
            200,
            params={"steps": 3}
        )
        
        if success:
            data = response.json()
            if 'steps_executed' in data and 'final_result' in data:
                print(f"   ✓ Executed {data['steps_executed']} steps")
                final_result = data['final_result']
                if final_result:
                    print(f"   Status: {final_result.get('status', 'unknown')}")
                    print(f"   Time: {final_result.get('time', 0):.2f}s")
                    print(f"   Events: {final_result.get('event_count', 0)}")
                return True
        return False

    def test_simulation_state(self):
        """Test getting simulation state"""
        if not self.simulation_id:
            print("   ⚠ No simulation ID available, skipping state test")
            return False
            
        success, response = self.run_test(
            "Get Simulation State",
            "GET",
            f"simulation/{self.simulation_id}/state",
            200
        )
        
        if success:
            data = response.json()
            if 'id' in data and 'time' in data:
                print(f"   ✓ Retrieved state for simulation {data['id']}")
                print(f"   Current time: {data.get('time', 0):.2f}s")
                print(f"   Altitude: {data.get('altitude', 0):.1f}m")
                print(f"   Events generated: {data.get('events_generated', 0)}")
                return True
        return False

    def test_simulation_reset(self):
        """Test simulation reset"""
        if not self.simulation_id:
            print("   ⚠ No simulation ID available, skipping reset test")
            return False
            
        success, response = self.run_test(
            "Reset Simulation",
            "POST",
            f"simulation/{self.simulation_id}/reset",
            200
        )
        
        if success:
            data = response.json()
            if data.get('status') == 'reset':
                print(f"   ✓ Successfully reset simulation {self.simulation_id}")
                return True
        return False

    def test_list_simulations(self):
        """Test listing all simulations"""
        success, response = self.run_test(
            "List Simulations",
            "GET",
            "simulations",
            200
        )
        
        if success:
            data = response.json()
            if 'simulations' in data:
                print(f"   ✓ Found {len(data['simulations'])} active simulations")
                return True
        return False

    def test_experiment_create(self):
        """Test experiment creation"""
        experiment_data = {
            "name": f"Test Experiment {datetime.now().strftime('%H%M%S')}",
            "description": "Automated test experiment",
            "config": {
                "terrain_type": "lunar",
                "initial_altitude": 800.0,
                "descent_velocity": 40.0,
                "vibration_amplitude": 0.3,
                "noise_level": 0.05,
                "feature_density": 150
            }
        }
        
        success, response = self.run_test(
            "Create Experiment",
            "POST",
            "experiment/create",
            200,
            data=experiment_data
        )
        
        if success:
            data = response.json()
            if 'id' in data and 'name' in data:
                self.experiment_id = data['id']
                print(f"   ✓ Created experiment: {data['name']} (ID: {self.experiment_id})")
                return True
        return False

    def test_list_experiments(self):
        """Test listing experiments"""
        success, response = self.run_test(
            "List Experiments",
            "GET",
            "experiments",
            200
        )
        
        if success:
            data = response.json()
            if 'experiments' in data:
                print(f"   ✓ Found {len(data['experiments'])} experiments")
                return True
        return False

    def test_ai_analysis_simulation(self):
        """Test AI analysis on simulation"""
        if not self.simulation_id:
            print("   ⚠ No simulation ID available, skipping AI analysis test")
            return False
            
        # First run a few simulation steps to generate data
        print("   Running simulation steps for AI analysis...")
        for i in range(3):
            requests.post(f"{self.base_url}/simulation/{self.simulation_id}/step", 
                         params={"steps": 5}, timeout=10)
            time.sleep(0.5)
        
        analysis_data = {
            "simulation_id": self.simulation_id,
            "analysis_type": "simulation"
        }
        
        success, response = self.run_test(
            "AI Analysis - Simulation",
            "POST",
            "ai/analyze",
            200,
            data=analysis_data
        )
        
        if success:
            data = response.json()
            if 'enabled' in data:
                if data['enabled']:
                    print(f"   ✓ AI analysis completed")
                    if 'analysis' in data:
                        print(f"   Analysis preview: {str(data['analysis'])[:100]}...")
                else:
                    print(f"   ⚠ AI analysis disabled: {data.get('message', 'No message')}")
                return True
        return False

    def test_ai_analysis_suggestion(self):
        """Test AI parameter suggestions"""
        suggestion_data = {
            "analysis_type": "suggestion",
            "target_accuracy": 2.0
        }
        
        success, response = self.run_test(
            "AI Analysis - Parameter Suggestions",
            "POST",
            "ai/analyze",
            200,
            data=suggestion_data
        )
        
        if success:
            data = response.json()
            if 'enabled' in data:
                if data['enabled']:
                    print(f"   ✓ AI suggestions generated")
                    if 'suggestions' in data:
                        print(f"   Suggestions preview: {str(data['suggestions'])[:100]}...")
                else:
                    print(f"   ⚠ AI suggestions disabled: {data.get('message', 'No message')}")
                return True
        return False

    def test_simulation_validation_errors(self):
        """Test simulation creation with invalid data"""
        print("\n--- Testing Validation Errors ---")
        
        # Test 1: Invalid terrain type
        success1, _ = self.run_test(
            "Invalid Terrain Type",
            "POST",
            "simulation/create",
            200,  # Should still work with default fallback
            data={"terrain_type": "invalid_terrain"}
        )
        
        # Test 2: Negative altitude
        success2, _ = self.run_test(
            "Negative Altitude",
            "POST",
            "simulation/create",
            422,  # Validation error expected
            data={"initial_altitude": -100}
        )
        
        # Test 3: Invalid noise level
        success3, _ = self.run_test(
            "Invalid Noise Level",
            "POST",
            "simulation/create",
            422,  # Validation error expected
            data={"noise_level": 2.0}  # Should be 0-1
        )
        
        return success1 and success2 and success3

    def test_nonexistent_simulation(self):
        """Test operations on non-existent simulation"""
        fake_id = "nonexistent-simulation-id"
        
        success1, _ = self.run_test(
            "Step Non-existent Simulation",
            "POST",
            f"simulation/{fake_id}/step",
            404
        )
        
        success2, _ = self.run_test(
            "Get Non-existent Simulation State",
            "GET",
            f"simulation/{fake_id}/state",
            404
        )
        
        return success1 and success2

    def cleanup_simulation(self):
        """Clean up created simulation"""
        if self.simulation_id:
            try:
                requests.delete(f"{self.base_url}/simulation/{self.simulation_id}", timeout=10)
                print(f"   🧹 Cleaned up simulation {self.simulation_id}")
            except:
                print(f"   ⚠ Failed to cleanup simulation {self.simulation_id}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 LANDINGOS API TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.tests_run}")
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"   - {test}")
        
        print("="*60)

def main():
    print("="*60)
    print("🚀 LANDINGOS API TESTING")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = LandingOSAPITester()
    
    try:
        # Basic API Tests
        print("\n--- Basic API Tests ---")
        tester.test_terrain_types()
        tester.test_terrain_features()
        tester.test_ai_status()
        
        # Simulation Tests
        print("\n--- Simulation Tests ---")
        tester.test_simulation_create()
        tester.test_simulation_step()
        tester.test_simulation_state()
        tester.test_list_simulations()
        tester.test_simulation_reset()
        
        # Experiment Tests
        print("\n--- Experiment Tests ---")
        tester.test_experiment_create()
        tester.test_list_experiments()
        
        # AI Analysis Tests
        print("\n--- AI Analysis Tests ---")
        tester.test_ai_analysis_simulation()
        tester.test_ai_analysis_suggestion()
        
        # Error Handling Tests
        print("\n--- Error Handling Tests ---")
        tester.test_simulation_validation_errors()
        tester.test_nonexistent_simulation()
        
    finally:
        # Cleanup
        print("\n--- Cleanup ---")
        tester.cleanup_simulation()
    
    # Print summary
    tester.print_summary()
    
    # Return exit code
    return 0 if tester.tests_failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())