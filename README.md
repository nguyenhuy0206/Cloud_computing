# Pipeline MLOps End-to-End cho Edge AI trên Azure IoT Edge

## 0) Phase 1 MVP (Bản demo đang chạy được)
Repository hiện đã có MVP bằng Python, chạy local được:
- Vòng lặp suy luận (inference) giả lập ở edge
- Lớp gửi telemetry theo chế độ `mock` hoặc `azure`
- Payload telemetry có `prediction`, `confidence`, `inference_ms`, `timestamp`

### Chạy nhanh
1. Chạy từ thư mục project:
```bash
cp .env.example .env
python3 run.py
```
2. Chạy test:
```bash
python3 -m unittest tests/test_inference.py tests/test_pipeline.py
```

### Chạy chế độ Azure (tùy chọn)
Nếu muốn gửi telemetry lên Azure IoT Hub thật:
1. Cài dependency:
```bash
pip install azure-iot-device
```
2. Cập nhật `.env`:
```env
CLOUD_MODE=azure
IOT_HUB_DEVICE_CONNECTION_STRING=<your-device-connection-string>
```
3. Chạy:
```bash
python3 run.py
```

## 1) Ý tưởng dự án đã tinh chỉnh
Xây dựng một hệ thống MLOps thu gọn nhưng thực tế: model được train trên cloud, đóng gói thành edge workload, triển khai xuống thiết bị edge, theo dõi (monitoring), và cập nhật phiên bản an toàn theo rollout.

Trọng tâm demo theo ghi chú nhóm:
- Triển khai model `v1` lên thiết bị camera edge
- Cập nhật từ xa lên model `v2` qua Azure
- Đo latency, độ ổn định và khả năng rollback

## 2) Mục tiêu dự án
Tạo pipeline tự động kết nối:
- Huấn luyện/đóng gói model phía cloud
- Build image và push registry qua CI/CD
- Triển khai thiết bị qua Azure IoT Edge
- Monitoring runtime và vòng lặp cập nhật/retrain

## 3) Phạm vi
Trong phạm vi:
- Một prototype end-to-end
- Một edge inference module chạy trên thiết bị mục tiêu
- Rollout model theo phiên bản (canary + full rollout)
- Dashboard theo dõi và cảnh báo cơ bản
- Chiến lược rollback khi kiểm tra sức khỏe thất bại

Ngoài phạm vi (giai đoạn mini-project):
- HA đa vùng production
- Cổng quản trị RBAC đa tenant phức tạp
- Tối ưu orchestration cho fleet quy mô lớn

## 4) Tóm tắt kiến trúc
- **Training**: Azure ML (hoặc luồng export nhanh từ Edge Impulse)
- **Artifact/Image**: Azure Container Registry (ACR)
- **Device Gateway**: Azure IoT Hub + IoT Edge runtime
- **Deployment**: IoT Edge module manifest theo phiên bản
- **Monitoring**: Azure Monitor / Application Insights + IoT telemetry

Xem chi tiết tại [ARCHITECTURE.md](/Users/phongpham/Downloads/Cloud Computing/project/ARCHITECTURE.md).

## 5) Cấu trúc repository đề xuất
```text
project/
  docs/
    diagrams/
    adr/
  infra/
    bicep/
    terraform/          # chọn một IaC stack chính
  ml/
    data/
    training/
    evaluation/
    export/
  edge/
    modules/
      inference-module/
      telemetry-module/
    deployment/
      manifests/
  ci/
    github-actions/
    azure-devops/
  scripts/
  tests/
    integration/
    edge/
  README.md
  REQUIREMENTS.md
  ARCHITECTURE.md
  DEVELOPMENT_PLAN.md
  TODO.md
```

## 6) Bản đồ tài liệu
- [REQUIREMENTS.md](/Users/phongpham/Downloads/Cloud Computing/project/REQUIREMENTS.md): Yêu cầu chức năng/phi chức năng và tiêu chí thành công
- [ARCHITECTURE.md](/Users/phongpham/Downloads/Cloud Computing/project/ARCHITECTURE.md): Kiến trúc hệ thống, luồng dữ liệu, quyết định thiết kế
- [DEVELOPMENT_PLAN.md](/Users/phongpham/Downloads/Cloud Computing/project/DEVELOPMENT_PLAN.md): Kế hoạch triển khai theo giai đoạn
- [TODO.md](/Users/phongpham/Downloads/Cloud Computing/project/TODO.md): Checklist công việc thực thi
