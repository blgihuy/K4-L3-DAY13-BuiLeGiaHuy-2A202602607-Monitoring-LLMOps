# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms` (SLO <= 3000ms)
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng phải chờ lâu hơn trước khi nhận câu trả lời, trải nghiệm ứng dụng bị suy giảm.
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian bắt đầu tăng đột biến.
  2. Lọc `data/logs.jsonl` trong khoảng thời gian đó, lấy một `correlation_id` có `latency_ms > 3000`.
  3. Mở trace có cùng `correlation_id` trên Langfuse, đối chiếu waterfall các child span (`retrieval` vs `generation`) để định vị bước nào gây nghẽn (ví dụ span `retrieval` bị chậm).
- Mitigation tạm thời: Khởi động lại cache/kết nối vector store hoặc fallback sang truy vấn không dùng RAG; nếu do prompt version mới làm tăng output/suy luận thì rollback prompt label `production` về version ổn định trước.
- Owner: `student-2A202602607`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Tỉ lệ lỗi request (`error_rate_pct`) và tỉ lệ retrieval thành công (`retrieval_success_rate_pct`)
- Điều kiện và thời gian duy trì: `error_rate_pct > 2%` hoặc `retrieval_success_rate_pct < 90%` trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng nhận lỗi HTTP 500 hoặc không nhận được câu trả lời từ AI agent.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors trên dashboard để xác định tỉ lệ lỗi và các `error_type` chính.
  2. Lọc `data/logs.jsonl` tìm event `request_failed` có `tool_success: false`, lấy `correlation_id` và chi tiết exception.
  3. Mở trace cùng `correlation_id` trên Langfuse để xem span nào bị fail và thông báo lỗi tương ứng.
- Mitigation tạm thời: Bật chế độ degraded/fallback cho agent (bỏ qua retrieval nếu vector store timeout `tool_fail`); kiểm tra kết nối mạng và tài nguyên backend; rollback bản deploy nếu xảy ra sau khi cập nhật code.
- Owner: `student-2A202602607`

## Alert 3

- Tên: `CostBudgetSpike`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Chi phí mô hình (`cost_usd`) và số lượng tokens tiêu thụ (`tokens_in`, `tokens_out`) so với ngân sách $2.5/ngày.
- Điều kiện và thời gian duy trì: `total_cost_usd > 2.5` trong 1 giờ hoặc `sum(cost_usd) > 0.05` mỗi phút trong 5 phút
- Ảnh hưởng tới người dùng: Ngân sách API cạn kiệt nhanh chóng, có thể khiến tài khoản bị đình chỉ hoặc rate-limit hàng loạt.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Cost và Tokens trên dashboard để xác định thời điểm chi phí tăng vọt và xem nguyên nhân do input tokens hay output tokens.
  2. Lọc `data/logs.jsonl` tìm request có `cost_usd` hoặc `tokens_out` bất thường (ví dụ incident `cost_spike`).
  3. Mở trace trên Langfuse kiểm tra span `generation`, xem chi tiết token breakdown và prompt version đang chạy.
- Mitigation tạm thời: Thiết lập giới hạn trần `max_tokens` cho câu trả lời; nếu candidate prompt mới gây sinh văn bản quá dài thì ngay lập tức rollback label `production` về prompt version cũ; chặn các mẫu câu hỏi bất thường có dấu hiệu tấn công lặp từ.
- Owner: `student-2A202602607`
