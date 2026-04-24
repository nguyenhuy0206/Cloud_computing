import os
import requests
import time
import shutil

API_KEY = ""
DATA_PATH = "data/to_upload"
UPLOADED_PATH = "data/uploaded"
LABEL = "fish"

def upload_to_edge_impulse(file_path):
    file_name = os.path.basename(file_path)
    
    # Endpoint CHUẨN cho hình ảnh là /files chứ không phải /data
    url = 'https://ingestion.edgeimpulse.com/api/training/files'
    
    headers = {
        'x-api-key': API_KEY,
        'x-label': LABEL,
    }
    
    with open(file_path, 'rb') as f:
        files = {'data': (file_name, f, 'image/jpeg')}
        
        try:
            res = requests.post(url, headers=headers, files=files)
            
            if res.status_code == 200:
                print(f" [OK] Uploaded: {file_name}")
                shutil.move(file_path, os.path.join(UPLOADED_PATH, file_name))
            else:
                print(f" [Error] {file_name}: {res.status_code} - {res.text}")
        except Exception as e:
            print(f" [Critical Error] {str(e)}")


def monitor_and_upload():
    print(f"--- MLOps Uploader Started: Watching {DATA_PATH} ---")
    while True:
        files = [f for f in os.listdir(DATA_PATH) if f.endswith(('.jpg', '.jpeg', '.png'))]
        
        if files:
            print(f"Found {len(files)} new images. Starting upload...")
            for f in files:
                full_path = os.path.join(DATA_PATH, f)
                upload_to_edge_impulse(full_path)
                time.sleep(0.5) 
        
        time.sleep(10)

if __name__ == "__main__":
    monitor_and_upload()