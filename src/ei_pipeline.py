import requests
import time
import os
import sys
from azure.storage.blob import BlobServiceClient

API_KEY = ""
ORG_ID = ""
PIPELINE_ID = ""
PROJECT_ID = ""
AZURE_CONN_STR = "" 
IMG_CONTAINER = "img"
MODEL_CONTAINER = "models"
IMG_FOLDER = "unlabeled/"
THRESHOLD = 20 
TWJ_KEY = ""
ARCH = "runner-linux-aarch64" 
IMPUSLE_ID = "1"
HEADERS = {"x-api-key": API_KEY, "Accept": "application/json", "Content-Type": "application/json"}
FLAG_JOB = 0 

def get_last_pipeline_run():
    url = f"https://studio.edgeimpulse.com/v1/api/organizations/{ORG_ID}/pipelines/{PIPELINE_ID}"
    try:
        headers = {"x-jwt-token": TWJ_KEY}
        res = requests.get(url, headers=headers).json()
        if res["success"]:
            last_run_id = res["pipeline"]["lastRun"]["id"]
            return last_run_id
    except Exception as e:
        print(f"\n[Cant connect to Edge Impulse API]: {e}")
    return None

def is_ei_busy():
    url = f"https://studio.edgeimpulse.com/v1/api/{PROJECT_ID}/jobs"
    try:
        res = requests.get(url, headers=HEADERS).json()
        active_jobs = res.get("jobs", [])
        if not active_jobs:
            return False
        else: 
            return True
        
    except Exception as e:
        print(f"\n[Cant connect to Edge Impulse API]: {e}")
        return True

def get_azure_count():
    try:
        client = BlobServiceClient.from_connection_string(AZURE_CONN_STR)
        container = client.get_container_client(IMG_CONTAINER)
        return sum(1 for _ in container.list_blobs(name_starts_with=IMG_FOLDER))
    except Exception as e:
        print(f"\n[LỖI AZURE]: {e}")
        return -1

def trigger_pipeline():
    url = f"https://studio.edgeimpulse.com/v1/api/organizations/{ORG_ID}/pipelines/{PIPELINE_ID}/run"
    headers = {
    "x-api-key": "ei_3cbe11ce5b7fb01da4468900003d7099f9ce1857cb3efbeb",
    "Accept": "application/json",
    "Content-Type": "application/json",
    }
    res = requests.post(url, headers=headers)
    if res.status_code == 200:
        print(f"Response trigger pipeline:", res["pipelineRun"]["id"])


def get_list_deployments():
    url = f"https://studio.edgeimpulse.com/v1/api/{PROJECT_ID}/deployment/history?impulseId={IMPUSLE_ID}"
    res = requests.get(url, headers=HEADERS).json()
    versions = res.get("totalDeploymentCount", 0)
    return versions

def download_model(version):
    url = f"https://studio.edgeimpulse.com/v1/api/{PROJECT_ID}/deployment/history/{version}/download"
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            with open("model.eim", "wb") as f:
                f.write(res.content)
            print(" Download model successfully.")
    except Exception as e:
        print(f"Error downloading model: {e}")
   
        
def upload_to_azure(file_path, blob_name):
    try:
        client = BlobServiceClient.from_connection_string(AZURE_CONN_STR)
        container = client.get_container_client(MODEL_CONTAINER)
        with open(file_path, "rb") as data:
            container.upload_blob(name=blob_name, data=data, overwrite=True)
        print(f"Uploaded {blob_name}")
        return True
    except Exception as e:
        print(f"Error uploading to Azure: {e}")
        return False    


def run_retrain(flag_job):
    last_version = get_list_deployments()
    print("Last deployment version:", last_version)

    current_azure_count = get_azure_count()
    if current_azure_count == -1: return
    target_count = current_azure_count + THRESHOLD
    print(f"Have {current_azure_count} images. Target: {target_count} images.")

    while True:
        current_count = get_azure_count()
        if current_count > current_azure_count:
            diff = current_count - (target_count - THRESHOLD)
            if current_count >= target_count:
                print("\n\n[Enough new images]")

                if is_ei_busy() or flag_job == 1:
                    print("Edge Impulse has Jobs running. Waiting for it to finish...")
                else:
                    flag_job = 1
                    print(" Starting new pipeline run...")
                    trigger_pipeline()
                    
                    while True:
                        new_version = get_list_deployments()
                        
                        if new_version and new_version > last_version:
                            print(f"\n -> New deployment detected! Version: {new_version}")
                            
                            model_path = "model.eim"
                            download_model(new_version) 
                            
                            if os.path.exists(model_path):
                                if upload_to_azure(model_path, "model.eim"):
                                    print("Update model in Azure successfully.")
                                    
                                    last_version = new_version
                                    target_count = current_count + THRESHOLD
                                    print(f"Target={target_count} images.")
                                    break 
                            else:
                                print("Error: Model file not found after download.")
                                break
                        
                        print(".", end="", flush=True)
                        time.sleep(30)
            flag_job = 0
        time.sleep(10)

if __name__ == "__main__":
    flag = 0
    try:
        run_retrain(flag)
    except KeyboardInterrupt:
        print("\n\nStop")
        sys.exit(0)