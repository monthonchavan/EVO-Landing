#!/usr/bin/env python3
"""
Enhanced LandingOS Backend API Testing
Tests SNN processing, 3D visualization, batch experiments, and enhanced features
"""

import requests
import sys
import time
import json
from datetime import datetime

class LandingOSEnhancedTester:
    def __init__(self, base_url="https://links-1.preview.emergentagent.com/api/landingos"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failed_tests = []
        self.simulation_id = None
        self.experiment_id = None

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
                response = requests.get(url, headers=headers, params=params, timeout=20)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params, timeout=20)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=20)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=20)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        # Show key fields for debugging
                        important_keys = ['id', 'status', 'enabled', 'experiments_completed', 'corners_detected', 'features_tracked']
                        shown_data = {k: v for k, v in response_data.items() if k in important_keys}
                        if shown_data:
                            print(f"   Key data: {shown_data}")
                    return True, response
                except:
                    print(f"   Response: {response.text[:150]}...")
                    return True, response
            else:
                self.tests_failed += 1
                self.failed_tests.append(name)
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response: {response.text[:200]}")
                return False, response

        except requests.exceptions.Timeout:
            self.tests_failed += 1
            self.failed_tests.append(name)
            print(f"❌ Failed - Request timeout after 20s")
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

    def test_ai_status_disabled(self):
        """Test that AI status returns enabled: false"""
        success, response = self.run_test(
            "AI Status (Should be Disabled)",
            "GET",
            "ai/status",
            200
        )
        if success:
            data = response.json()
            if data.get('enabled') == False:
                print(f"   ✓ AI is correctly disabled: {data.get('message', '')}")
                return True
            else:
                print(f"   ❌ AI should be disabled but got: {data}")
                return False
        return False

    def test_simulation_create_with_snn(self):
        """Test simulation creation with SNN processing enabled"""
        config_data = {
            "terrain_type": "lunar",
            "initial_altitude": 1000.0,
            "descent_velocity": 50.0,
            "vibration_amplitude": 1.5,
            "vibration_frequency": 15.0,
            "noise_level": 0.2,
            "feature_density": 250,
            "use_snn_processing": True
        }
        
        success, response = self.run_test(
            "Create Simulation with SNN Processing",
            "POST",
            "simulation/create",
            200,
            data=config_data
        )
        
        if success:
            data = response.json()
            if 'id' in data and 'status' in data:
                self.simulation_id = data['id']
                print(f"   ✓ Created SNN simulation: {self.simulation_id}")
                print(f"   Status: {data['status']}")
                print(f"   Altitude: {data['altitude']}m")
                return True
            else:
                print(f"   ❌ Missing required fields in response: {data}")
        return False

    def test_simulation_step_with_snn_data(self):
        """Test simulation stepping with SNN corner detection and feature tracking"""
        if not self.simulation_id:
            print("   ⚠ No simulation ID available, skipping SNN step test")
            return False
            
        success, response = self.run_test(
            "Step Simulation with SNN Data",
            "POST",
            f"simulation/{self.simulation_id}/step",
            200,
            params={"steps": 5}
        )
        
        if success:
            data = response.json()
            if 'steps_executed' in data and 'final_result' in data:
                print(f"   ✓ Executed {data['steps_executed']} steps")
                final_result = data['final_result']
                if final_result:
                    print(f"   Status: {final_result.get('status', 'unknown')}")
                    print(f"   Events generated: {final_result.get('event_count', 0)}")
                    print(f"   Corners detected: {final_result.get('corners_detected', 0)}")
                    print(f"   Features tracked: {final_result.get('features_tracked', 0)}")
                    
                    # Check for SNN-specific data
                    if 'corners_detected' in final_result and 'features_tracked' in final_result:
                        print("   ✓ SNN processing data present")
                        return True
                    else:
                        print("   ❌ Missing SNN processing data")
        return False

    def test_3d_data_endpoint(self):
        """Test 3D visualization data endpoint"""
        if not self.simulation_id:
            print("   ⚠ No simulation ID available, skipping 3D data test")
            return False
            
        success, response = self.run_test(
            "Get 3D Visualization Data",
            "GET",
            f"simulation/{self.simulation_id}/3d",
            200
        )
        
        if success:
            data = response.json()
            required_fields = ['terrain', 'trajectory', 'current_pose']
            
            if all(field in data for field in required_fields):
                print("   ✓ All required 3D fields present")
                
                # Check terrain data
                terrain = data.get('terrain', {})
                if 'heightmap' in terrain and 'features' in terrain:
                    heightmap = terrain['heightmap']
                    if 'data' in heightmap and 'width' in heightmap and 'height' in heightmap:
                        print(f"   ✓ Heightmap: {heightmap['width']}x{heightmap['height']}")
                    print(f"   ✓ Terrain features: {len(terrain['features'])} items")
                
                # Check trajectory data
                trajectory = data.get('trajectory', {})
                if 'ground_truth' in trajectory and 'estimated' in trajectory:
                    gt_count = len(trajectory['ground_truth'])
                    est_count = len(trajectory['estimated'])
                    print(f"   ✓ Trajectory points - GT: {gt_count}, Estimated: {est_count}")
                
                # Check current pose
                pose = data.get('current_pose', {})
                if all(k in pose for k in ['x', 'y', 'z', 'roll', 'pitch', 'yaw']):
                    print(f"   ✓ Current pose: ({pose['x']:.1f}, {pose['y']:.1f}, {pose['z']:.1f})")
                
                return True
            else:
                missing = [f for f in required_fields if f not in data]
                print(f"   ❌ Missing 3D data fields: {missing}")
        return False

    def test_batch_experiment_presets(self):
        """Test batch experiment presets endpoint"""
        success, response = self.run_test(
            "Get Batch Experiment Presets",
            "GET",
            "experiments/presets",
            200
        )
        
        if success:
            data = response.json()
            if isinstance(data, dict) and len(data) > 0:
                print(f"   ✓ Found {len(data)} preset experiment types")
                
                # Check for expected presets
                expected_presets = ['lunar_baseline', 'lunar_high_vibration', 'snn_vs_standard']
                found_presets = []
                for preset_name in expected_presets:
                    if preset_name in data:
                        found_presets.append(preset_name)
                        print(f"   ✓ Preset '{preset_name}' available")
                
                if len(found_presets) >= 2:
                    print("   ✓ Core presets available")
                    return True
                else:
                    print(f"   ❌ Missing expected presets. Found: {list(data.keys())}")
            else:
                print(f"   ❌ Invalid preset data format: {type(data)}")
        return False

    def test_run_batch_experiment(self):
        """Test running a batch experiment"""
        experiment_configs = [
            {
                "name": "Test SNN Lunar",
                "terrain_type": "lunar",
                "initial_altitude": 800.0,
                "descent_velocity": 45.0,
                "vibration_amplitude": 1.0,
                "noise_level": 0.15,
                "use_snn_processing": True
            },
            {
                "name": "Test Standard Lunar", 
                "terrain_type": "lunar",
                "initial_altitude": 800.0,
                "descent_velocity": 45.0,
                "vibration_amplitude": 1.0,
                "noise_level": 0.15,
                "use_snn_processing": False
            }
        ]
        
        success, response = self.run_test(
            "Run Batch Experiment",
            "POST",
            "experiments/run",
            200,
            data=experiment_configs
        )
        
        if success:
            data = response.json()
            if 'experiments_completed' in data and 'results' in data:
                completed = data['experiments_completed']
                results = data['results']
                print(f"   ✓ Completed {completed} experiments")
                
                if len(results) >= 2:
                    for i, result in enumerate(results):
                        name = result.get('name', f'Experiment {i+1}')
                        pos_err = result.get('final_position_error', 'N/A')
                        att_err = result.get('final_attitude_error', 'N/A') 
                        duration = result.get('duration', 'N/A')
                        print(f"   ✓ {name}: pos_err={pos_err}, att_err={att_err}, duration={duration}s")
                    
                    print("   ✓ Batch experiment results contain comparison data")
                    return True
                else:
                    print(f"   ❌ Expected at least 2 results, got {len(results)}")
            else:
                print(f"   ❌ Missing batch experiment result fields: {data}")
        return False

    def test_run_preset_experiment(self):
        """Test running a preset experiment"""
        success, response = self.run_test(
            "Run Preset Experiment",
            "POST",
            "experiments/run-preset/lunar_baseline",
            200
        )
        
        if success:
            data = response.json()
            if 'preset' in data and 'experiments_completed' in data and 'results' in data:
                print(f"   ✓ Ran preset '{data['preset']}'")
                print(f"   ✓ Completed {data['experiments_completed']} experiments")
                
                results = data['results']
                if results and len(results) > 0:
                    result = results[0]
                    print(f"   ✓ Result: pos_err={result.get('final_position_error', 'N/A')}")
                    return True
                else:
                    print("   ❌ No results in preset experiment")
            else:
                print(f"   ❌ Invalid preset experiment response: {data}")
        return False

    def test_list_batch_experiments(self):
        """Test listing batch experiments"""
        success, response = self.run_test(
            "List Batch Experiments",
            "GET",
            "experiments/list",
            200
        )
        
        if success:
            data = response.json()
            if isinstance(data, dict):
                print(f"   ✓ Retrieved batch experiment list")
                return True
            elif isinstance(data, list):
                print(f"   ✓ Retrieved {len(data)} batch experiments")
                return True
            else:
                print(f"   ❌ Unexpected data format: {type(data)}")
        return False

    def test_enhanced_simulation_features(self):
        """Test enhanced simulation features like terrain, noise filtering"""
        if not self.simulation_id:
            print("   ⚠ No simulation ID, creating one for enhanced features test")
            self.test_simulation_create_with_snn()
        
        if not self.simulation_id:
            return False
        
        # Test simulation state with enhanced data
        success, response = self.run_test(
            "Enhanced Simulation State",
            "GET",
            f"simulation/{self.simulation_id}/state",
            200
        )
        
        if success:
            data = response.json()
            enhanced_fields = ['events_generated', 'time', 'altitude']
            
            if all(field in data for field in enhanced_fields):
                print(f"   ✓ Enhanced simulation data present")
                print(f"   Events generated: {data.get('events_generated', 0)}")
                print(f"   Simulation time: {data.get('time', 0):.2f}s")
                print(f"   Current altitude: {data.get('altitude', 0):.1f}m")
                
                # Check for terrain and config data
                if 'terrain_heightmap' in data or 'config' in data:
                    print("   ✓ Extended state data available")
                
                return True
            else:
                missing = [f for f in enhanced_fields if f not in data]
                print(f"   ❌ Missing enhanced fields: {missing}")
        return False

    def test_error_handling(self):
        """Test error handling for invalid requests"""
        print("\n--- Testing Error Handling ---")
        
        # Test invalid simulation ID for 3D data
        success1, _ = self.run_test(
            "3D Data - Invalid Simulation ID",
            "GET",
            "simulation/invalid-id/3d",
            404
        )
        
        # Test invalid preset experiment
        success2, _ = self.run_test(
            "Invalid Preset Experiment",
            "POST",
            "experiments/run-preset/nonexistent_preset",
            404
        )
        
        # Test malformed batch experiment data
        success3, _ = self.run_test(
            "Malformed Batch Experiment",
            "POST", 
            "experiments/run",
            422,  # Validation error expected
            data=[{"invalid": "config"}]
        )
        
        return success1 and success2 and success3

    def cleanup_resources(self):
        """Clean up test resources"""
        if self.simulation_id:
            try:
                requests.delete(f"{self.base_url}/simulation/{self.simulation_id}", timeout=10)
                print(f"   🧹 Cleaned up simulation {self.simulation_id}")
            except:
                print(f"   ⚠ Failed to cleanup simulation {self.simulation_id}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("📊 LANDINGOS ENHANCED FEATURES TEST SUMMARY")
        print("="*70)
        print(f"Total Tests: {self.tests_run}")
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        
        if self.tests_run > 0:
            success_rate = (self.tests_passed/self.tests_run*100)
            print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests ({len(self.failed_tests)}):")
            for test in self.failed_tests:
                print(f"   - {test}")
        else:
            print("\n✅ All tests passed!")
        
        print("="*70)

def main():
    print("="*70)
    print("🚀 LANDINGOS ENHANCED BACKEND API TESTING")
    print("  Testing: SNN Processing, 3D Data, Batch Experiments")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Use backend URL from frontend/.env
    tester = LandingOSEnhancedTester()
    
    try:
        # Test AI status (should be disabled)
        print("\n=== AI Status Tests ===")
        tester.test_ai_status_disabled()
        
        # Test SNN-enhanced simulation
        print("\n=== SNN Processing Tests ===")
        tester.test_simulation_create_with_snn()
        tester.test_simulation_step_with_snn_data()
        
        # Test 3D visualization data
        print("\n=== 3D Visualization Tests ===")
        tester.test_3d_data_endpoint()
        
        # Test batch experiments
        print("\n=== Batch Experiment Tests ===")
        tester.test_batch_experiment_presets()
        tester.test_run_batch_experiment()
        tester.test_run_preset_experiment()
        tester.test_list_batch_experiments()
        
        # Test enhanced simulation features
        print("\n=== Enhanced Features Tests ===")
        tester.test_enhanced_simulation_features()
        
        # Test error handling
        print("\n=== Error Handling Tests ===")
        tester.test_error_handling()
        
    except KeyboardInterrupt:
        print("\n⚠ Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
    finally:
        # Cleanup
        print("\n=== Cleanup ===")
        tester.cleanup_resources()
    
    # Print summary
    tester.print_summary()
    
    # Return appropriate exit code
    return 0 if tester.tests_failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())