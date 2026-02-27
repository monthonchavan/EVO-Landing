#!/usr/bin/env python3
"""
Quick LandingOS Backend Test - Individual API Testing
"""

import requests
import json

def test_api(url, method="GET", data=None, timeout=10):
    """Test individual API endpoint"""
    print(f"\n🔍 Testing: {method} {url}")
    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout, headers={'Content-Type': 'application/json'})
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if isinstance(result, dict):
                    print(f"   Keys: {list(result.keys())}")
                    # Show important data
                    if 'enabled' in result:
                        print(f"   Enabled: {result['enabled']}")
                    if 'id' in result:
                        print(f"   ID: {result['id']}")
                    if 'experiments_completed' in result:
                        print(f"   Experiments: {result['experiments_completed']}")
                elif isinstance(result, list):
                    print(f"   List length: {len(result)}")
                print("   ✅ SUCCESS")
                return True, result
            except json.JSONDecodeError:
                print(f"   Response: {response.text[:100]}")
                print("   ✅ SUCCESS (non-JSON)")
                return True, response.text
        else:
            print(f"   Error: {response.text[:200]}")
            print("   ❌ FAILED")
            return False, None
            
    except requests.Timeout:
        print("   ❌ TIMEOUT")
        return False, None
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False, None

def main():
    base_url = "https://links-1.preview.emergentagent.com/api/landingos"
    
    print("🚀 LandingOS API Quick Test")
    print("="*50)
    
    # 1. AI Status (should be disabled)
    test_api(f"{base_url}/ai/status")
    
    # 2. Create simulation with SNN
    sim_config = {
        "terrain_type": "lunar",
        "initial_altitude": 1000.0,
        "descent_velocity": 50.0,
        "vibration_amplitude": 1.0,
        "use_snn_processing": True
    }
    success, sim_result = test_api(f"{base_url}/simulation/create", "POST", sim_config)
    
    sim_id = None
    if success and isinstance(sim_result, dict) and 'id' in sim_result:
        sim_id = sim_result['id']
        print(f"\n📝 Simulation ID: {sim_id}")
        
        # 3. Step simulation
        test_api(f"{base_url}/simulation/{sim_id}/step?steps=3", "POST")
        
        # 4. Get 3D data
        test_api(f"{base_url}/simulation/{sim_id}/3d")
        
        # 5. Get simulation state 
        test_api(f"{base_url}/simulation/{sim_id}/state")
    
    # 6. Batch experiment presets
    test_api(f"{base_url}/experiments/presets")
    
    # 7. Simple batch experiment (reduced size)
    simple_batch = [
        {
            "name": "Quick Test",
            "terrain_type": "lunar", 
            "initial_altitude": 500.0,
            "descent_velocity": 80.0,  # Faster for quick test
            "use_snn_processing": True
        }
    ]
    print(f"\n🧪 Testing batch experiment with quick config...")
    test_api(f"{base_url}/experiments/run", "POST", simple_batch, timeout=30)
    
    # 8. List batch experiments
    test_api(f"{base_url}/experiments/list")
    
    print("\n" + "="*50)
    print("✅ Quick test completed!")

if __name__ == "__main__":
    main()