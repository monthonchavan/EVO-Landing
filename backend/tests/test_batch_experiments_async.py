"""
Test batch experiments async API endpoints
Tests the async batch experiments feature with background tasks and polling
"""
import pytest
import requests
import time
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://links-1.preview.emergentagent.com').rstrip('/')


class TestPhdThesis:
    """Test PhD thesis PDF availability"""
    
    def test_phd_thesis_accessible(self):
        """Test that PhD thesis PDF is accessible"""
        response = requests.get(f"{BASE_URL}/PhD_Thesis_Event_Driven_Navigation.pdf", stream=True)
        assert response.status_code == 200, f"PhD thesis not accessible: {response.status_code}"
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        assert 'pdf' in content_type.lower() or response.content[:4] == b'%PDF', "Response is not a PDF"
        print(f"✓ PhD thesis accessible - size: {len(response.content)} bytes")


class TestBatchExperimentsPresets:
    """Test batch experiment presets endpoint"""
    
    def test_get_presets(self):
        """Test presets endpoint returns available presets"""
        response = requests.get(f"{BASE_URL}/api/landingos/experiments/presets")
        assert response.status_code == 200
        
        data = response.json()
        assert 'lunar_baseline' in data, "lunar_baseline preset missing"
        assert data['lunar_baseline']['name'] == 'Lunar Baseline'
        print(f"✓ Got {len(data)} presets")


class TestBatchExperimentsAsyncRun:
    """Test async batch experiment run API"""
    
    def test_run_experiment_returns_task_id_immediately(self):
        """Test that POST /api/landingos/experiments/run returns task_id immediately"""
        payload = [{
            "name": "TEST_async_batch",
            "terrain_type": "lunar",
            "initial_altitude": 300,
            "descent_velocity": 20,
            "vibration_amplitude": 0.2,
            "noise_level": 0.05,
            "use_snn_processing": True
        }]
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/landingos/experiments/run", json=payload)
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify immediate response (not waiting for experiment completion)
        assert elapsed_time < 3, f"Response took too long ({elapsed_time:.2f}s) - should be immediate"
        
        # Verify response structure
        assert 'task_id' in data, "task_id missing from response"
        assert 'status' in data, "status missing from response"
        assert data['status'] == 'pending', f"Expected pending status, got {data['status']}"
        assert 'poll_url' in data, "poll_url missing from response"
        
        print(f"✓ Got task_id immediately: {data['task_id']}")
        
        # Store task_id for polling test
        return data['task_id']
    
    def test_run_preset_returns_task_id_immediately(self):
        """Test that POST /api/landingos/experiments/run-preset/{name} returns task_id immediately"""
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/landingos/experiments/run-preset/lunar_baseline")
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify immediate response
        assert elapsed_time < 3, f"Response took too long ({elapsed_time:.2f}s) - should be immediate"
        
        # Verify response structure
        assert 'task_id' in data
        assert 'preset' in data
        assert data['preset'] == 'lunar_baseline'
        
        print(f"✓ Preset task started: {data['task_id']}")


class TestBatchExperimentsTaskPolling:
    """Test task status polling endpoints"""
    
    @pytest.fixture
    def task_id(self):
        """Create a task and return its ID"""
        payload = [{
            "name": "TEST_polling",
            "terrain_type": "lunar",
            "initial_altitude": 200,
            "descent_velocity": 15,
            "vibration_amplitude": 0.1,
            "noise_level": 0.02,
            "use_snn_processing": True
        }]
        response = requests.post(f"{BASE_URL}/api/landingos/experiments/run", json=payload)
        return response.json()['task_id']
    
    def test_poll_task_status(self, task_id):
        """Test GET /api/landingos/experiments/task/{task_id} returns status"""
        response = requests.get(f"{BASE_URL}/api/landingos/experiments/task/{task_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert 'task_id' in data
        assert 'status' in data
        assert data['status'] in ['pending', 'running', 'completed', 'failed']
        
        print(f"✓ Task status: {data['status']}")
    
    def test_poll_nonexistent_task_returns_404(self):
        """Test polling non-existent task returns 404"""
        response = requests.get(f"{BASE_URL}/api/landingos/experiments/task/nonexistent-task-id")
        assert response.status_code == 404
        print("✓ Non-existent task returns 404")
    
    def test_results_before_completion_returns_400(self, task_id):
        """Test getting results before task completion returns 400"""
        # First verify task is not completed yet
        status_response = requests.get(f"{BASE_URL}/api/landingos/experiments/task/{task_id}")
        if status_response.json()['status'] == 'completed':
            pytest.skip("Task already completed")
        
        # Try to get results
        response = requests.get(f"{BASE_URL}/api/landingos/experiments/task/{task_id}/results")
        assert response.status_code == 400
        print("✓ Results before completion returns 400")


class TestBatchExperimentsTaskResults:
    """Test getting task results after completion"""
    
    @pytest.fixture
    def completed_task_id(self):
        """Create a fast task and wait for completion"""
        payload = [{
            "name": "TEST_fast_completion",
            "terrain_type": "lunar",
            "initial_altitude": 150,
            "descent_velocity": 10,
            "vibration_amplitude": 0.1,
            "noise_level": 0.01,
            "use_snn_processing": True
        }]
        response = requests.post(f"{BASE_URL}/api/landingos/experiments/run", json=payload)
        task_id = response.json()['task_id']
        
        # Poll until completion (max 60s)
        for _ in range(30):
            status_resp = requests.get(f"{BASE_URL}/api/landingos/experiments/task/{task_id}")
            if status_resp.json()['status'] == 'completed':
                return task_id
            time.sleep(2)
        
        pytest.skip("Task did not complete in time")
    
    def test_get_results_after_completion(self, completed_task_id):
        """Test GET /api/landingos/experiments/task/{task_id}/results returns results"""
        response = requests.get(f"{BASE_URL}/api/landingos/experiments/task/{completed_task_id}/results")
        assert response.status_code == 200
        
        data = response.json()
        assert 'results' in data
        assert 'experiment_ids' in data
        assert len(data['results']) > 0
        
        # Validate result structure
        result = data['results'][0]
        assert 'id' in result
        assert 'name' in result
        assert 'final_position_error' in result
        assert 'final_attitude_error' in result
        
        print(f"✓ Got results: position_error={result['final_position_error']:.4f}m")


class TestBatchExperimentsCompareAsync:
    """Test async comparison endpoint"""
    
    @pytest.fixture
    def two_completed_experiments(self):
        """Create two experiments and wait for completion"""
        exp_ids = []
        
        for i in range(2):
            payload = [{
                "name": f"TEST_compare_{i}",
                "terrain_type": "lunar",
                "initial_altitude": 100 + i * 50,
                "descent_velocity": 8 + i,
                "vibration_amplitude": 0.1,
                "noise_level": 0.01,
                "use_snn_processing": True
            }]
            response = requests.post(f"{BASE_URL}/api/landingos/experiments/run", json=payload)
            task_id = response.json()['task_id']
            
            # Wait for completion
            for _ in range(30):
                status_resp = requests.get(f"{BASE_URL}/api/landingos/experiments/task/{task_id}")
                status_data = status_resp.json()
                if status_data['status'] == 'completed':
                    exp_ids.extend(status_data['experiment_ids'])
                    break
                time.sleep(2)
        
        if len(exp_ids) < 2:
            pytest.skip("Not enough experiments completed")
        
        return exp_ids
    
    def test_compare_returns_task_id_immediately(self, two_completed_experiments):
        """Test POST /api/landingos/experiments/compare returns task_id immediately"""
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/landingos/experiments/compare",
            json=two_completed_experiments
        )
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 3, f"Response too slow: {elapsed:.2f}s"
        
        data = response.json()
        assert 'task_id' in data
        assert 'poll_url' in data
        
        print(f"✓ Comparison task started: {data['task_id']}")
        return data['task_id']
    
    def test_comparison_results(self, two_completed_experiments):
        """Test full comparison flow with polling"""
        # Start comparison
        response = requests.post(
            f"{BASE_URL}/api/landingos/experiments/compare",
            json=two_completed_experiments
        )
        task_id = response.json()['task_id']
        
        # Poll for completion
        for _ in range(15):
            status_resp = requests.get(f"{BASE_URL}/api/landingos/experiments/comparison/{task_id}")
            if status_resp.json()['status'] == 'completed':
                break
            time.sleep(1)
        
        # Get results
        results_resp = requests.get(f"{BASE_URL}/api/landingos/experiments/comparison/{task_id}/results")
        assert results_resp.status_code == 200
        
        data = results_resp.json()
        assert 'experiments' in data
        assert 'best_position_accuracy' in data
        
        print(f"✓ Comparison complete with {len(data['experiments'])} experiments")


class TestBatchExperimentsTasksList:
    """Test listing all tasks"""
    
    def test_list_tasks(self):
        """Test GET /api/landingos/experiments/tasks returns task list"""
        response = requests.get(f"{BASE_URL}/api/landingos/experiments/tasks")
        assert response.status_code == 200
        
        data = response.json()
        assert 'batch_tasks' in data
        assert 'comparison_tasks' in data
        
        print(f"✓ Found {len(data['batch_tasks'])} batch tasks, {len(data['comparison_tasks'])} comparison tasks")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
