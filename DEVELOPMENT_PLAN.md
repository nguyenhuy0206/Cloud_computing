# Kế Hoạch Triển Khai

## 1) Kế hoạch theo giai đoạn

### Phase 0: Setup và Baseline (Tuần 1)
- Chốt phạm vi, thiết bị mục tiêu và ngưỡng metrics
- Tạo tài nguyên Azure: IoT Hub, ACR, workspace monitoring
- Chuẩn bị cấu trúc repo và skeleton CI

Điều kiện hoàn thành:
- Cloud resources đã sẵn sàng và pipeline truy cập được
- Team build/push được test container image

### Phase 1: ML Baseline và Edge Runtime (Tuần 2)
- Xây workflow train model baseline
- Export model cho runtime inference ở edge
- Tạo prototype inference module trên thiết bị mục tiêu

Điều kiện hoàn thành:
- Inference module chạy local trên hardware mục tiêu
- Có số liệu baseline accuracy/latency ban đầu

### Phase 2: CI/CD và Deployment Automation (Tuần 3)
- Tạo pipeline tự động build/test/push
- Tạo IoT Edge deployment manifest theo version
- Deploy `v1` qua IoT Hub cho nhóm canary

Điều kiện hoàn thành:
- `git push` có thể kích hoạt build image và sinh deployment artifact
- Canary device nhận và chạy được `v1`

### Phase 3: Observability và Quality Gates (Tuần 4)
- Bổ sung telemetry cho latency, prediction, module health
- Cấu hình dashboard Azure Monitor/App Insights
- Thêm health gate và rollback logic

Điều kiện hoàn thành:
- Dashboard hiển thị metrics realtime từ thiết bị
- Khi health check fail thì rollback hoạt động

### Phase 4: Demo cập nhật model `v2` (Tuần 5)
- Train hoặc tinh chỉnh model `v2`
- Canary rollout cho `v2`
- Validate luồng nâng cấp và fallback

Điều kiện hoàn thành:
- Cập nhật từ xa `v1 -> v2` thành công
- Kịch bản rollback được tài liệu hóa và tái chạy được

### Phase 5: Hoàn thiện deliverables (Tuần 6)
- Tổng hợp kiến trúc và kết quả
- Chuẩn bị demo script và báo cáo đánh giá ngắn
- Chốt bộ tài liệu cuối

Điều kiện hoàn thành:
- Tất cả deliverables bắt buộc hoàn tất

## 2) Workstreams
- **ML Workstream**: data prep, training, evaluation, export
- **Platform Workstream**: IoT Hub, ACR, manifest, CI/CD
- **Edge Workstream**: runtime module, telemetry, fallback logic
- **Observability Workstream**: dashboard, alerting, operational checks

## 3) Rủi ro và phương án giảm thiểu
- Hiệu năng hardware thấp:
  - Dùng model nhẹ hơn và giảm input resolution
- Mạng không ổn định:
  - Inference offline + retry telemetry có buffer
- Sai cấu hình deployment:
  - Validate manifest ở staging/canary trước full rollout
- Trễ tiến độ:
  - Ưu tiên một vertical slice hoàn chỉnh trước khi mở rộng

## 4) Deliverables
1. Prototype MLOps end-to-end chạy được
2. Một edge deployment có thể cập nhật version
3. Dashboard theo dõi metrics chính
4. Báo cáo đánh giá (latency, accuracy, độ tin cậy deployment)
