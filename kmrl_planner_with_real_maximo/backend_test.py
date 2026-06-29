import requests
import json

BASE_URL = "http://localhost:8000"

def test_trainsets_list():
    r = requests.get(f"{BASE_URL}/trainsets/")
    assert r.status_code == 200, f"Trainsets list failed with {r.status_code}"
    data = r.json()
    assert isinstance(data, list), "Trainsets response not a list"
    print(f"Trainsets count: {len(data)}")

def test_iot_sensor():
    code = "KM01"
    r = requests.get(f"{BASE_URL}/iot/trainsets/{code}")
    assert r.status_code == 200, f"IoT sensor fetch failed: {r.status_code}"
    data = r.json()
    print(f"IoT Data for {code}: {data}")

def test_run_plan():
    r = requests.post(f"{BASE_URL}/plans/run", json={})
    assert r.status_code == 200, f"Run plan failed: {r.status_code}"
    data = r.json()
    print("Plan Run Output Sample:")
    print(json.dumps(data, indent=2))

def test_ml_predict_fitness():
    payload = {
        "sensor_aggregate": 55.0,
        "days_since_inspection": 10,
        "open_job_card_count": 1
    }
    r = requests.post(f"{BASE_URL}/ml/predict_fitness_expiry", json=payload)
    assert r.status_code == 200, f"ML fitness predict failed: {r.status_code}"
    print("ML Fitness Expiry Prediction:", r.json())

def test_ml_predict_urgency():
    payload = {"description": "brake overheating detected at bogie 3"}
    r = requests.post(f"{BASE_URL}/ml/maintenance_urgency", json=payload)
    assert r.status_code == 200, f"ML urgency predict failed: {r.status_code}"
    print("ML Maintenance Urgency Prediction:", r.json())

def test_ml_csv_upload(endpoint, file_path):
    files = {'file': open(file_path, 'rb')}
    r = requests.post(f"{BASE_URL}{endpoint}", files=files)
    assert r.status_code == 200, f"CSV upload failed for {endpoint}: {r.status_code}"
    print(f"CSV Upload {endpoint} Results Sample:")
    print(json.dumps(r.json()['results'][:3], indent=2))  # Print first 3 results

if __name__ == "__main__":
    print("Testing Trainsets List...")
    test_trainsets_list()
    
    print("\nTesting IoT Sensor Endpoint...")
    test_iot_sensor()
    
    print("\nTesting Plan Run Endpoint...")
    test_run_plan()
    
    print("\nTesting ML Fitness Expiry Prediction...")
    test_ml_predict_fitness()
    
    print("\nTesting ML Maintenance Urgency Prediction...")
    test_ml_predict_urgency()
    
    print("\nTesting ML CSV Upload Endpoints...")
    # Adjust paths to your local test CSVs
    test_ml_csv_upload("/ml/csv/certificate_expiry/", "test_data/test_certificate_expiry.csv")
    test_ml_csv_upload("/ml/csv/maintenance_urgency/", "test_data/test_jobcard_urgency.csv")
