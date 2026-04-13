# TODO

## Phase 1 MVP - 5 việc ưu tiên ngay
- [ ] Thay `InferenceEngine` giả lập bằng runtime model thật (Edge Impulse export hoặc tương đương)
- [ ] Thêm adapter camera/frame input (ưu tiên đọc từ file trước, sau đó live sensor)
- [ ] Bật gửi telemetry thật lên Azure IoT Hub trong môi trường staging
- [ ] Thêm integration test cho chuyển đổi chế độ `mock`/`azure` từ `.env`
- [ ] Đóng gói MVP bằng Docker để demo chạy nhất quán

## Việc cần chốt ngay
- [ ] Chốt phần cứng demo cuối: ESP32-CAM trực tiếp hay qua edge gateway
- [ ] Chốt loại bài toán ML (classification/detection) và bộ dữ liệu baseline
- [ ] Chốt hướng training chính: Azure ML, Edge Impulse, hoặc hybrid
- [ ] Chốt hệ CI chính: GitHub Actions hay Azure DevOps

## Cloud Setup
- [ ] Tạo Azure resource group cho dự án
- [ ] Provision IoT Hub và đăng ký test device(s)
- [ ] Provision ACR và cấp quyền push cho pipeline
- [ ] Setup Azure Monitor / Application Insights workspace

## Edge Module
- [ ] Hoàn thiện camera input + preprocessing trong inference module
- [ ] Tích hợp model export `v1` và xác minh inference local
- [ ] Chuẩn hóa telemetry payload (prediction, confidence, latency, health)
- [ ] Bổ sung retry queue an toàn khi offline

## CI/CD và Deployment
- [ ] Build container image theo commit/tag
- [ ] Push image semantic version lên ACR
- [ ] Sinh IoT Edge deployment manifest theo version
- [ ] Deploy canary group và xác minh health gate
- [ ] Promote từ canary ra full rollout

## Monitoring và Reliability
- [ ] Xây dashboard cho latency/error/drift/resource usage
- [ ] Định nghĩa ngưỡng alert để trigger rollback
- [ ] Tự động rollback về version ổn định trước đó
- [ ] Chạy chaos test: ngắt mạng và kiểm tra behavior

## Model Iteration
- [ ] Chuẩn bị dữ liệu retraining từ các edge case khó
- [ ] Train và validate `v2`
- [ ] Deploy `v2` qua đúng pipeline hiện có
- [ ] Ghi nhận chênh lệch hiệu năng `v1` vs `v2`

## Final Output
- [ ] Vẽ architecture diagram phục vụ thuyết trình
- [ ] Viết báo cáo đánh giá ngắn kèm bảng metrics
- [ ] Chuẩn bị demo script (happy path + rollback scenario)
- [ ] QA toàn bộ tài liệu và tính tái lập
