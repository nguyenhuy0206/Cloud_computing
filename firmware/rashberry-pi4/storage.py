import os
import time
from azure.storage.blob import BlobServiceClient

AZURE_CONNECTION_STRING = ""
CONTAINER_NAME = "fish-images"
LOCAL_FOLDER = "data/to_upload"

def upload_images_from_folder(folder_path):
    # 1. Khởi tạo kết nối
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)
    
    # Tạo container nếu chưa tồn tại
    try:
        container_client.create_container()
    except Exception:
        pass

    # 2. Duyệt qua tất cả các file trong thư mục
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not files:
        print(f" [!] Không tìm thấy ảnh trong {folder_path}")
        return

    print(f" [>] Tìm thấy {len(files)} ảnh. Bắt đầu tải lên...")

    for file_name in files:
        file_path = os.path.join(folder_path, file_name)
        
        # Tạo blob client cho từng file
        blob_client = container_client.get_blob_client(file_name)
        
        try:
            with open(file_path, "rb") as data:
                # Tải lên và ghi đè nếu trùng tên
                blob_client.upload_blob(data, overwrite=True)
            
            print(f" [OK] Đã tải lên: {file_name}")
            
            # (Tùy chọn) Xóa file local sau khi upload thành công để giải phóng bộ nhớ Pi
            # os.remove(file_path)
            
        except Exception as e:
            print(f" [Error] Không thể tải {file_name}: {e}")

if __name__ == "__main__":
    upload_images_from_folder(LOCAL_FOLDER)