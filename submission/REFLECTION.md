# Reflection — Lab 19

**Tên:** Phạm Tấn Gia Quốc (PhamTanGiaQuoc)  
**Cohort:** A2026 — Track 2  
**Path đã chạy:** both (Lite in-process & Docker/Engine ready)  

---

## Câu hỏi (≤ 200 chữ)

> Trên golden set 50 queries, mode nào thắng ở loại query nào (`exact` / `paraphrase` / `mixed`), và tại sao? Khi nào bạn **không** dùng hybrid (i.e. khi nào pure BM25 hoặc pure vector là lựa chọn đúng)?

Trên 50 golden queries:
- **`exact` (n=15):** BM25 thắng (96.7% vs 88.7% Vector). Từ khóa kỹ thuật trùng khớp nguyên văn (*verbatim*) giúp BM25 định vị chính xác tuyệt đối mà không bị nhiễu ngữ nghĩa.
- **`paraphrase` (n=15):** Vector/Semantic giải quyết tốt ngữ nghĩa tiềm ẩn khi dùng mô hình đa ngữ; tuy nhiên trên mô hình English-focused (bge-small), cả hai đều gặp thách thức (~24–33%).
- **`mixed` (n=20):** **Hybrid thắng áp đảo (100.0% vs 97.0% BM25 / 98.5% Vector)** nhờ RRF ($k=60$) cộng hưởng tín hiệu từ cả từ khóa thực thể và diễn đạt mở rộng, đưa Precision@10 tổng thể lên cao nhất (**78.6%**).

**Khi nào KHÔNG dùng Hybrid:**
1. **Dùng Pure BM25:** Khi cần SLA độ trễ siêu thấp (P99 < 3ms vs ~120ms của hybrid trên CPU) hoặc tra cứu mã lỗi/SKU/văn bản pháp lý cố định, tiết kiệm 100% chi phí suy luận vector.
2. **Dùng Pure Vector:** Khi tìm kiếm ý niệm trừu tượng/đa ngôn ngữ không có từ khóa rõ ràng hoặc hệ thống cần tối giản hạ tầng (chỉ duy trì 1 index duy nhất).

---

## Điều ngạc nhiên nhất khi làm lab này

Điều ấn tượng nhất là **Filtered Search Cliff**: post-filter làm recall sập từ 1.00 về 0.00 khi bộ lọc chọn lọc cao (~4% corpus), và Semantic Cache nếu quên namespace tenant sẽ tạo ra lỗ hổng bảo mật nghiêm trọng (OWASP LLM08) hoàn toàn im lặng không hề có báo lỗi.

---

## Bonus challenge

- [x] Đã làm bonus (xem `bonus/`: `ARCHITECTURE.md`, `agent.py`, `demo.py`)
- [ ] Pair work với: _Làm độc lập_
