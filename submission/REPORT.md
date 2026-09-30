# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Bùi Lê Gia Huy
- **MSSV:** 2A202602607
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/blgihuy/K4-L3-DAY13-BuiLeGiaHuy-2A202602607-Monitoring-LLMOps
- **Commit SHA cuối:** `61a34f827748393ced851ea7c9b412dd53dced23`
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602607`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 22/100 | 100/100 | Đạt điểm tuyệt đối: chuẩn schema JSON, correlation ID lan truyền, enrich context đầy đủ, PII sạch hoàn toàn |
| `validate_dashboard.py` | 6/6 | 6/6 panel | Đầy đủ 6 panel hợp lệ theo dashboard contract |
| `pytest` | 22 passed | 24 passed | 24/24 unit tests pass (bao gồm tests bổ sung cho CCCD và Credit Card) |
| Số traces hợp lệ | 1 | > 15 traces | Các trace có cấu trúc phân tầng cha-con đầy đủ: lab-agent-run -> retrieval, generation |
| Số PII leak | 0 (chưa load) | 0 leak | Không phát hiện rò rỉ Email, SĐT VN, CCCD, Thẻ thanh toán nào trong logs.jsonl |
| Latency P95 / TTFT P95 | ~500ms / 50ms | 2654ms / 50ms | Baseline 400-600ms; khi xảy ra sự cố rag_slow độ trễ P95 tăng lên 2654ms và TTFT giữ ổn định 50ms |
| Retrieval success rate | 100% | 100% | Toàn bộ các request retrieval hoàn thành thành công (không gặp lỗi exception ngoại trừ bị làm chậm 2.5s) |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Trong `app/middleware.py`, middleware `CorrelationIdMiddleware` xóa context cũ (`clear_contextvars()`), trích xuất header `x-request-id` nếu có hoặc tự động sinh mã định danh dạng `req-<8-char-hex>` bằng `uuid.uuid4().hex[:8]`. Sau đó bind ID vào contextvars thông qua `bind_contextvars(correlation_id=correlation_id)`, lưu vào `request.state.correlation_id` để truyền cho agent/trace, đồng thời trả lại `x-request-id` và `x-response-time-ms` trong response header.
- **Các metadata được ghi vào structured log:** Mỗi log record dạng JSON bao gồm các trường bắt buộc (`ts`, `level`, `service`, `event`, `correlation_id`, `env`), các trường context enrichment (`user_id_hash` băm sha256 12 ký tự từ user_id thực, `session_id`, `feature`, `model`), cùng các trường hiệu năng/chi phí (`latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`, `payload`).
- **Cách bảo đảm PII được scrub trước khi ghi:** Cấu hình processor `scrub_event` trong chuỗi structlog processors tại `app/logging_config.py` ngay trước khi ghi ra file qua `JsonlFileProcessor`. Processor duyệt qua các trường text/payload và áp dụng regex từ `app/pii.py` để thay thế thông tin nhạy cảm (Email, SĐT Việt Nam các định dạng, CCCD 12 số, Credit Card) thành `[REDACTED_<TYPE>]`. Hàm `summarize_text` cũng chủ động scrub trước khi tạo preview.
- **Cách kiểm chứng kết quả:** Chạy bộ kiểm thử unit test `pytest` (24/24 tests pass bao gồm các test case cho Email, Phone VN, CCCD, Credit Card) và chạy `scripts/validate_logs.py` trên file log sinh ra từ `scripts/load_test.py`, đạt điểm tối đa 100/100 (0 record thiếu required fields, 0 record thiếu enrichment, 10 unique correlation IDs, 0 PII leak detected).

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Project Langfuse cá nhân mang tên `day13-k4-l3b-2A202602607`. Trong các trace, metadata đều chứa `correlation_id` (định dạng `req-<8-hex>`), `environment: dev`, `user_id_hash` và `feature`, hoàn toàn khớp 1-1 với request và structured log trên máy cục bộ.
- **Cấu trúc root/retrieval/generation observations:**
  ```text
  day13-agent-request
  └── lab-agent-run (agent root span)
      ├── retrieval (retriever child span)
      └── generation (generation child span với model, usage, cost và prompt version)
  ```
- **Cách nối trace với log:** Sử dụng trường `correlation_id` được sinh từ middleware (`req-<8-hex>`), vừa được ghi vào structured log (`data/logs.jsonl`) vừa được truyền vào metadata của trace Langfuse thông qua `propagate_attributes(metadata={"correlation_id": correlation_id})`.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1 (`labels: ['baseline', 'production']`)
- **Version/label candidate:** Version 2 (`labels: ['candidate', 'latest']`)
- **Trace ID của mỗi version:**
  - Trace ID dùng Version 1 (baseline/production): `300bd77bc1068090b508eead7888843c` (request `req-9c00d44b`)
  - Trace ID dùng Version 2 (candidate): `9c00e6c4e62034e0f8fa513228aa20a3` (request `req-98125cce`)
- **Cách promote và rollback `production`:** Dùng script `python scripts/manage_prompts.py promote` (gán label `production` sang version 2) hoặc thao tác trên Langfuse UI; và `python scripts/manage_prompts.py rollback` (gán lại label `production` về version 1), sau đó restart API để xóa cache prompt 60s và gửi request xác nhận.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dựng dashboard hoàn chỉnh gồm 6 panels tuân thủ contract `config/dashboard.yaml`: (1) Latency (P50, P95, P99, TTFT P95), (2) Traffic (Request count, rate/min), (3) Errors & Retrieval (Error rate %, Tool success rate %, Error types), (4) Cost (Total cost, cost/min), (5) Tokens (Tokens in, tokens out, total tokens), (6) Quality (Mean quality proxy score). Giao diện trực quan chạy tại `http://127.0.0.1:8000/dashboard` và file tĩnh `submission/evidence/dashboard.html` với auto-refresh 30s và time range 60 phút.
- **SLO và lý do chọn:** Chọn SLO 99.5% request đạt trạng thái thành công và latency <= 3000ms trong rolling window 28 ngày. Lý do: dựa trên baseline hệ thống có latency trung bình ~400-600ms (P95 < 1000ms), ngưỡng 3000ms đảm bảo phát hiện kịp thời các sự cố tắc nghẽn (như `rag_slow`) trong khi vẫn đáp ứng kỳ vọng thời gian phản hồi của người dùng cuối.
- **Cách tính error budget:** Với SLO 99.5%, error budget là 0.5%. Nếu giả định quy mô lưu lượng đạt 10,000 request trong cửa sổ 28 ngày, hệ thống cho phép tối đa 50 request bị lỗi hoặc có latency vượt quá 3000ms. Khi tiêu thụ hết ngân sách lỗi này (burn rate cao), đội ngũ phát triển phải dừng release tính năng mới để ưu tiên khắc phục độ ổn định.
- **Ba alert và runbook tương ứng:**
  1. `HighLatencyP95` (severity: `warning`, duration: `5m`): Kích hoạt khi P95 latency > 3000ms trong 5 phút. Runbook: Kiểm tra panel latency -> lọc log line `response_sent` có `latency_ms > 3000` -> mở trace kiểm tra child span `retrieval` vs `generation` -> mitigation bằng cách restart cache/kết nối vector store hoặc rollback prompt nếu candidate prompt mới gây chậm.
  2. `HighErrorRate` (severity: `critical`, duration: `5m`): Kích hoạt khi error rate > 2% hoặc retrieval success < 90% trong 5 phút. Runbook: Kiểm tra panel errors -> lọc log `request_failed` lấy `correlation_id` và `error_type` -> mở trace kiểm tra span lỗi -> bật chế độ degraded fallback bypass retrieval nếu vector store timeout (`tool_fail`).
  3. `CostBudgetSpike` (severity: `warning`, duration: `5m`): Kích hoạt khi tổng chi phí > $2.5 trong 1h hoặc > $0.05/phút trong 5 phút. Runbook: Kiểm tra panel cost và tokens -> lọc log tìm request có `cost_usd` hoặc `tokens_out` tăng vọt -> mở trace kiểm tra span `generation` -> thiết lập trần max_tokens hoặc rollback prompt nếu candidate mới gây suy luận quá dài dòng.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** Khoảng 03:50:00 UTC đến 03:54:00 UTC (10:50:00 - 10:54:00 GMT+7) ngày 30/09/2026.
- **Triệu chứng từ metrics:** Panel Latency trên Dashboard ghi nhận độ trễ P95 tăng vọt từ baseline ~400-600ms lên tới **2654ms** (khi chạy concurrency 5, thời gian xử lý toàn batch lên tới hơn 13,200ms), vi phạm ngưỡng cảnh báo và đẩy trạng thái Panel Latency vào mức BREACH. Trong khi đó, tỷ lệ lỗi Error Rate vẫn ở mức 0% và lượng token tiêu thụ hoàn toàn bình thường.
- **Log line và correlation ID liên quan:**
  - `correlation_id`: `req-9d277080` (session `k4-l3b-challenge-s03`, feature `monitoring`).
  - Log line `request_received`: `{"service": "api", "payload": {"message_preview": "Summarize the observability workflow for an AI API."}, "event": "request_received", "correlation_id": "req-9d277080", "env": "dev", "feature": "monitoring", "model": "claude-sonnet-4-5", "session_id": "k4-l3b-challenge-s03", "user_id_hash": "189d0a182d4e", "level": "info", "ts": "2026-09-30T03:50:31.460682Z"}`
  - Log line `response_sent`: `{"service": "api", "latency_ms": 2654, "ttft_ms": 50, "tokens_in": 35, "tokens_out": 122, "cost_usd": 0.001935, "quality_score": 0.8, "tool_name": "retrieval", "tool_success": true, "payload": {"answer_preview": "Starter answer. You should improve this output logic and add better quality chec..."}, "event": "response_sent", "correlation_id": "req-9d277080", "env": "dev", "feature": "monitoring", "model": "claude-sonnet-4-5", "session_id": "k4-l3b-challenge-s03", "user_id_hash": "189d0a182d4e", "level": "info", "ts": "2026-09-30T03:50:34.121264Z"}`
- **Trace ID và span gây ảnh hưởng:**
  - Trace ID: `9bebaf9a07d2eed38a44c5f5b02e1417`
  - Span gây ảnh hưởng: Child span `retrieval` (loại `RETRIEVER`, observation ID `922474ce78bb2aaa`) có độ trễ lên tới **2.507s** (chiếm 94.2% tổng thời gian 2.661s của root span `lab-agent-run`), trong khi child span `generation` chỉ mất **0.154s** (154ms).
- **Root cause:** Sự cố `rag_slow` ở tầng Vector Database Retrieval: hàm tìm kiếm tài liệu `retrieve()` gặp hiện tượng nghẽn tài nguyên và chậm trễ nhân tạo 2.5s khi tìm kiếm tài liệu liên quan đến chủ đề `monitoring`.
- **Fix action:** Thực hiện tắt sự cố thông qua lệnh `python scripts/inject_incident.py --disable` (endpoint `/incidents/rag_slow/disable`). Kiểm tra lại ngay sau khi tắt cho thấy độ trễ hồi phục về mức baseline lý tưởng: `latency_ms: 154ms`. Trong production thực tế: kiểm tra tình trạng tải CPU/Memory của vector DB, khởi động lại kết nối connection pool và kích hoạt semantic cache.
- **Preventive measure:**
  1. Thiết lập circuit breaker và timeout cứng cho bước retrieval (ví dụ: `timeout=1.0s`), tự động fallback sang mô hình trả lời trực tiếp mà không dừng request.
  2. Bật alert rule `HighLatencyP95` đã định cấu hình trong `config/alert_rules.yaml` để cảnh báo tức thì qua Slack `#k4-l3b-alerts` khi P95 latency > 3000ms trong 5 phút.
  3. Bổ sung metric đo lường riêng biệt thời gian của tầng retrieval (`retrieval_latency_ms`) để phân tách rõ ràng với tầng sinh câu trả lời LLM.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Quyết định thực hiện PII scrubbing tự động ở tầng Structlog Processor (`scrub_event`) trước khi ghi file/render JSON, kết hợp với việc che giấu thông tin ngay khi tóm tắt preview. Lý do: bảo đảm nguyên tắc defense-in-depth, tránh việc bỏ sót PII nếu lập trình viên quên scrub thủ công ở từng route handler, giúp log và trace luôn an toàn tuyệt đối trước khi rời khỏi memory.
- **Một lỗi/blocker đã gặp:** Khi bắt đầu lab, baseline validator chỉ đạt 22/100 do thiếu cơ chế lan truyền correlation ID, chưa làm giàu ngữ cảnh (enrichment) và còn lộ PII thô (email, SĐT, số thẻ). Ngoài ra, trên Windows PowerShell gặp lỗi mã hóa ký tự Unicode cp1252 khi in log/CLI và kết nối tới Langfuse Cloud đôi lúc bị timeout tạm thời.
- **Cách tìm nguyên nhân và xử lý:** Đọc kỹ schema contract và validator script; hoàn thiện `CorrelationIdMiddleware` với chuẩn `req-<8-hex>`; cấu hình `configure_utf8_stdio()` cho console Windows; triển khai bộ lọc regex khử PII đệ quy; và cấu hình retry/fallback cho Langfuse prompt client để đảm bảo ứng dụng luôn chạy ổn định kể cả khi mạng gián đoạn.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  1. *Metrics:* Cung cấp bức tranh toàn cảnh cấp hệ thống (aggregated overview), giúp phát hiện triệu chứng (symptoms) và xác định chính xác thời điểm xảy ra sự cố (ví dụ: Panel Latency P95 tăng vọt từ 500ms lên 2650ms).
  2. *Logs:* Giúp thu hẹp từ triệu chứng toàn cục về một request cụ thể thông qua việc lọc structured log tìm các bản ghi có độ trễ cao, từ đó trích xuất được `correlation_id` (ví dụ: `req-9d277080`).
  3. *Traces:* Phân rã request đó thành cây thực thi chi tiết (span waterfall tree), đo đạc thời gian từng bước để chỉ điểm chính xác mắt xích gây nghẽn (ví dụ: span `retrieval` chiếm 2.507s / 2.661s tổng thời gian xử lý), xác định root cause không thể chối cãi.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt trong LLMOps có tầm quan trọng tương đương mã nguồn ứng dụng vì ảnh hưởng trực tiếp tới chất lượng, latency, token và chi phí. Việc quản lý prompt version qua label (`production`, `candidate`) cho phép release và A/B testing mà không cần sửa code hay rebuild container. Nếu prompt mới gây thoái hóa (regression) hoặc làm tăng chi phí bất thường, ta có thể rollback label `production` về phiên bản cũ ngay lập tức. SLO và Error Budget cung cấp ranh giới định lượng giúp đội ngũ engineering biết khi nào hệ thống đủ an toàn để tiếp tục thử nghiệm và khi nào cần ưu tiên khắc phục độ tin cậy.
- **Điều quan trọng nhất đã học:** Hiểu sâu sắc và làm chủ phương pháp luận Observability cho AI/LLM: không chỉ giám sát tài nguyên máy chủ truyền thống mà phải giám sát ngữ cảnh thực thi (token in/out, cost USD, quality proxy, retrieval latency), biết cách trace cha-con và bảo vệ quyền riêng tư người dùng một cách triệt để.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Các thành phần LLM và RAG trong bài lab sử dụng mock; nếu triển khai môi trường production thật tế quy mô lớn cần tích hợp thêm Distributed Tracing (OpenTelemetry Collector), cơ chế Semantic Caching phân tán trên Redis để giảm tải vector DB, và hệ thống tự động hóa Canary Deployment kết hợp auto-rollback khi alert vi phạm SLO.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.

