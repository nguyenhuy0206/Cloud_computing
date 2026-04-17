# Kiến Trúc Hệ Thống

## 1) Kiểu kiến trúc
Hệ thống theo mô hình **hybrid cloud-native + edge**:
- Cloud xử lý vòng đời model, CI/CD, quản lý thiết bị và observability
- Edge xử lý inference thời gian thực và đảm bảo hoạt động khi mạng không ổn định

Cách này bám sát nguyên tắc Azure IoT reference architecture: tách module rõ ràng, triển khai độc lập, scale linh hoạt và bảo mật xuyên suốt.

## 2) Thành phần cấp cao

### Tầng Edge
- **IoT Edge Runtime** chạy trên thiết bị (với ESP32 có thể dùng gateway pattern khi cần)
- **Inference Module**: chạy model inference từ dữ liệu camera
- **Telemetry Module**: gửi kết quả dự đoán và chỉ số sức khỏe hệ thống
- **Fallback Logic**: hành vi an toàn cục bộ khi mất kết nối cloud

### Tầng Cloud
- **Azure IoT Hub**: định danh thiết bị, giao tiếp hai chiều, target deployment
- **Azure ML / Edge Impulse Export Path**: train/validate/export model
- **Azure Container Registry (ACR)**: lưu image inference theo version
- **CI/CD (GitHub Actions hoặc Azure DevOps)**: build, test, push, publish manifest
- **Azure Monitor / Application Insights**: metrics, logs, alerts
- **Storage/Analytics (tùy chọn)**: lưu dữ liệu cho retraining

## 3) Luồng dữ liệu và điều khiển chính

### A. Luồng training và đóng gói
1. Thu thập dữ liệu đã gán nhãn
2. Tiền xử lý và train model
3. Validate theo ngưỡng chấp nhận
4. Export model artifact
5. Build inference image và push ACR theo tag semantic (`v1.0.0`, `v1.1.0`)

### B. Luồng deployment
1. CI publish IoT Edge deployment manifest tham chiếu image tag trong ACR
2. IoT Hub rollout trước cho nhóm canary
3. Health gate kiểm tra latency/error/drift theo ngưỡng
4. Nếu đạt, rollout toàn bộ thiết bị
5. Nếu không đạt, rollback về manifest/image ổn định trước đó

### C. Luồng inference runtime
1. Dữ liệu camera đi vào inference module
2. Model dự đoán nhãn/điểm ngay trên edge
3. Kết quả + thời gian xử lý + metric tài nguyên được gửi telemetry
4. Cloud dashboard/alert theo dõi chất lượng vận hành

### D. Vòng lặp retrain
1. Thu thập các mẫu dự đoán lỗi hoặc khó từ telemetry
2. Làm sạch và tạo tập dữ liệu retraining
3. Train model mới (`v2`)
4. Lặp lại quy trình rollout theo giai đoạn

## 4) Kiến trúc bảo mật
- Mỗi thiết bị có danh tính riêng trong IoT Hub
- Cấp quyền tối thiểu cho registry và pipeline
- Giao tiếp cloud dùng TLS
- Chỉ dùng image từ nguồn ACR được kiểm soát
- Quản lý secrets qua biến CI an toàn / Key Vault

## 5) Độ tin cậy và vận hành
- **Offline-first**: inference vẫn chạy khi mất mạng tạm thời
- **Retry + backoff** cho telemetry
- **Canary deployment** để giảm blast radius
- **Automated rollback** theo tiêu chí thất bại
- **Giám sát xuyên suốt** cho cả edge và cloud

## 6) Quyết định thiết kế chính
- Tách module theo trách nhiệm (`inference`, `telemetry`, `deployment`) để dễ nâng cấp độc lập
- Ưu tiên rollout theo giai đoạn thay vì deploy toàn fleet ngay lập tức
- Xem observability là thành phần bắt buộc, không phải phụ trợ
- Bắt đầu bằng một vertical slice chạy được rồi mới mở rộng thiết bị
