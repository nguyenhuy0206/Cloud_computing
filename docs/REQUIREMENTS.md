# Yêu Cầu Hệ Thống

## 1) Yêu cầu chức năng (Functional Requirements)
1. Hệ thống phải train và validate được ít nhất một model ML cho edge inference.
2. Hệ thống phải đóng gói runtime inference thành workload có thể deploy.
3. Hệ thống phải publish artifact/image có version.
4. Hệ thống phải deploy được model `v1` lên ít nhất một thiết bị edge.
5. Hệ thống phải hỗ trợ cập nhật từ xa `v1 -> v2` qua Azure IoT deployment.
6. Hệ thống phải hỗ trợ rollout theo giai đoạn (canary rồi full rollout).
7. Hệ thống phải thu thập telemetry gồm: inference latency, prediction output, module health.
8. Hệ thống phải có dashboard monitoring và alert cơ bản.
9. Hệ thống phải hỗ trợ rollback về version ổn định trước đó.

## 2) Yêu cầu phi chức năng (Non-Functional Requirements)
1. **Latency**: p95 latency cho edge inference phải đạt ngưỡng mục tiêu của dự án.
2. **Availability**: inference cục bộ vẫn chạy khi cloud bị gián đoạn tạm thời.
3. **Security**: kết nối device-cloud phải mã hóa; không hardcode credentials.
4. **Maintainability**: deployment tái lập được thông qua CI/CD và quản lý manifest bằng version control.
5. **Scalability (mức demo)**: có thể mở rộng số lượng thiết bị mà không cần đổi thiết kế lớn.

## 3) Ràng buộc
- Thời gian và nhân lực nhóm có hạn
- Thiết bị edge có tài nguyên hạn chế
- Kết nối mạng có thể không ổn định
- Phạm vi là mini-project, chưa phải production đầy đủ

## 4) Giả định
- Có sẵn Azure subscription và quyền tạo tài nguyên
- Có ít nhất một thiết bị edge để demo
- Team truy cập được CI tooling (GitHub Actions hoặc Azure DevOps)
- Dữ liệu đủ chất lượng để đạt baseline accuracy

## 5) Tiêu chí thành công
1. Pipeline end-to-end chạy từ training tới deployment mà không cần thao tác thủ công rời rạc.
2. Thiết bị chạy được model `v1`, sau đó nâng cấp thành công lên `v2`.
3. Canary health gate hoạt động và chặn release lỗi.
4. Rollback thực thi được và có thể kiểm chứng.
5. Dashboard hiển thị được latency, health và prediction telemetry.

## 6) Checklist nghiệm thu
- [ ] Train model và tạo artifact có version
- [ ] Build và push edge image lên ACR
- [ ] Deploy `v1` lên canary device và xác nhận health
- [ ] Promote rollout sang nhóm thiết bị rộng hơn
- [ ] Deploy `v2` và xác nhận luồng cập nhật
- [ ] Mô phỏng lỗi và xác nhận rollback
- [ ] Xác nhận metrics hiển thị trên dashboard
