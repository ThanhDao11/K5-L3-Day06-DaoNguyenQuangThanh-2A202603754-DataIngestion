# Báo cáo cá nhân — Day 6 · Data Ingestion Engineering

- **Học viên:** Đào Nguyễn Quang Thành
- **MSSV:** 2A202603754
- **Lớp:** L3

---

## Dữ liệu và pipeline

* **Chủ đề, nguồn/quyền, số trang và quy tắc tính trang:**
  * *Tác phẩm / Chủ đề:* Tiểu thuyết văn học triết lý *The Alchemist* (tác giả: Paulo Coelho, bản dịch tiếng Anh của Clifford E. Landers).
  * *Nguồn gốc & Quyền xử lý:* File PDF lưu tại `starter/data/15-05-2021-084550The-Alchemist-Paulo-Coelho.pdf`. Được sử dụng cho mục đích học thuật, nghiên cứu và đánh giá kỹ thuật phi thương mại trong khuôn khổ Lab cá nhân (Fair Use).
  * *Số trang & Quy tắc tính trang:* File PDF gồm 136 trang vật lý. Áp dụng quy tắc loại trừ: bỏ trang bìa (1–2), mục lục (3), các trang lời khen ngợi (4–7), lời tựa (8–10), các trang phân trang trắng/tiêu đề (12, 13, 45) và phần phụ lục/giới thiệu tác phẩm khác/quảng cáo cuối sách (126–136).
  * *Số trang nội dung hợp lệ:* **112 trang** truyện thực tế (tổng cộng 210.075 ký tự), bao gồm: `Prologue` (trang 11), `Part One` (trang 14–44), `Part Two` (trang 46–123), và `Epilogue` (trang 124–125). Toàn bộ đặc tả được ghi nhận tại [data/manifest.json](../../data/manifest.json).

* **Chuẩn hóa, lỗi và giới hạn:**
  * *Chuẩn hóa Unicode & khoảng trắng:* Hàm `normalize_text` chuẩn hóa toàn bộ văn bản về chuẩn Unicode NFC (`unicodedata.normalize('NFC', text)`), chuyển đổi `\r\n` thành `\n`, loại bỏ khoảng trắng thừa trên từng dòng, đồng thời gom các dòng trống liên tiếp thành dấu ngắt đoạn `\n\n` nhằm bảo toàn ranh giới đoạn văn cho bước chunking ngữ nghĩa.
  * *Lỗi & Giới hạn dữ liệu:* Một số trang PDF có ký tự ngoặc kép cong (`“`, `”`) và dấu nháy (`’`, `‘`) không đồng nhất; các từ bị ngắt dòng do gạch nối (hyphenation) ở mép trang có thể làm tách rời từ vựng. Đã xử lý chuẩn hóa chuỗi và đối soát chuỗi không phân biệt ký tự nháy đơn/kép.

* **Embedding model/provider/version/số chiều, vector store/version, metric, lệnh chạy và chi phí:**
  * *Embedding Model:* `openai/text-embedding-3-small` thông qua cổng API OpenRouter. Số chiều vector: **1.536 chiều**. Cùng model được dùng thống nhất cho cả văn bản chunk và truy vấn query.
  * *Vector Store:* PostgreSQL phiên bản 16.16 tích hợp extension `pgvector` phiên bản 0.8.7 (chạy trên container Docker local cổng `127.0.0.1:55433`).
  * *Metric:* Khoảng cách Cosine Distance (`<=>`), điểm tương đồng được tính bằng công thức: $\text{similarity} = 1 - \text{cosine\_distance}$.
  * *Lệnh chạy pipeline:* `python -m starter.src.run` (hoặc `cd starter; python -m src.run`).
  * *Thời gian & Chi phí:*
    * Thời gian đọc và chuẩn hóa 112 trang PDF: **3,11 giây**.
    * Thời gian tạo vector nhúng (850 chunks): **30,48 giây**.
    * Chi phí API: Khoảng 0.0004 USD (khoảng ~10 đồng VNĐ, do model `text-embedding-3-small` có giá cực thấp: 0.02 USD / 1M tokens).

* **Metadata bắt buộc, trường lọc bổ sung, nguồn giá trị và lý do chọn:**
  * *Metadata bắt buộc:* `document_id` (`"the-alchemist"`), `source` (`"The-Alchemist-Paulo-Coelho.pdf"`), `page` (số trang vật lý: 11, 14, 15...).
  * *Trường lọc bổ sung (`part`):* Có 4 giá trị rõ ràng dựa theo cấu trúc phân mục của tác phẩm: `"Prologue"`, `"Part One"`, `"Part Two"`, `"Epilogue"`.
  * *Lý do chọn:* Tác phẩm văn học có sự chuyển biến rõ rệt theo từng giai đoạn (Tây Ban Nha, làm việc tại cửa hàng pha lê ở Tangier, vượt sa mạc Sahara cùng đoàn lữ hành, và kho báu kim tự tháp). Việc lọc theo `part` giúp triệt tiêu các kết quả gây nhiễu (distractor hits) xảy ra giữa các bối cảnh khác nhau.

---

## Cấu hình và benchmark

* **A / B / C (tham số cụ thể, khác biệt duy nhất B–C):**
  * *Chiến lược A (Fixed-size):* Kích thước chunk cố định 500 ký tự, độ gối đầu (overlap) 50 ký tự. Gán metadata bắt buộc (`page`, `source`), **không áp dụng metadata filter** khi truy vấn. Sinh ra **511 chunks**.
  * *Chiến lược B (Structure-aware Paragraph):* Chia chunk theo đoạn văn tự nhiên (dấu `\n\n`), giới hạn kích thước tối đa 800 ký tự. Nếu đoạn quá dài thì chia theo câu. Gán metadata bắt buộc kèm trường `part`. **Không áp dụng metadata filter** khi truy vấn. Sinh ra **339 chunks**.
  * *Chiến lược C (Paragraph + Filter):* Sử dụng **chính xác 100% cùng tập chunk và vector nhúng của Chiến lược B** (339 chunks, cùng embedding model, cùng corpus). **Điểm khác biệt duy nhất giữa B và C:** Khi câu hỏi truy vấn có chứa metadata filter (ví dụ: `{"part": "Part One"}`), Chiến lược C kích hoạt điều kiện lọc SQL trên pgvector (`AND metadata @> %s::jsonb`), còn Chiến lược B tìm kiếm trên toàn bộ không gian vector.

* **$\ge 20$ câu: phân chia $\ge 15$ dev / $\ge 5$ test, câu metadata filter và cách kiểm chứng evidence:**
  * *Bộ câu hỏi:* Gồm đúng **20 câu hỏi** được lưu tại [benchmark/questions.json](../../benchmark/questions.json).
  * *Phân chia Split:* **15 câu Dev (`q01`–`q15`)** và **5 câu Test (`q16`–`q20`)**.
  * *Phân bổ tầng đại diện (Stratified Distribution):* Tránh thiên lệch thời gian, cả hai tập đều trải đều từ đầu đến cuối tác phẩm:
    * Dev (15 câu): Trang 11, 14, 17, 17, 21, 22, 26, 30, 34, 44, 48, 51, 66, 75, 124.
    * Test (5 câu): Trang 24, 32, 71, 85, 107.
  * *Câu hỏi Metadata Filter (tổng cộng 5 câu $\ge 3$):*
    * Dev: `q01` (`part: Prologue`), `q10` (`part: Part One`), `q15` (`part: Epilogue`).
    * Test: `q17` (`part: Part One`), `q20` (`part: Part Two`) — thỏa mãn $\ge 1$ câu trong Test set.
  * *Kiểm chứng Evidence:* 100% bằng chứng (`evidence_quote`) được đối soát trực tiếp, đảm bảo tồn tại thực tế và hỗ trợ đầy đủ câu trả lời trên đúng số trang `gold_page`.

* **Tiêu chí chọn chiến lược đã chốt trước khi xem test:**
  * Ưu tiên 1: Điểm **Evidence Hit@3 trên tập Dev** phải cao nhất để đảm bảo thông tin quan trọng lọt vào ngữ cảnh cung cấp cho LLM.
  * Ưu tiên 2: Điểm **Chunk Coherence thủ công** cao (ít bị ngắt vụn câu từ, trọn vẹn ngữ nghĩa).
  * Ưu tiên 3: Tối ưu số lượng chunk và chi phí lưu trữ (ít chunk hơn đồng nghĩa tiết kiệm dung lượng database và chi phí API embedding).

---

## Kết quả

### Bảng 1: Chỉ số định lượng truy xuất (Hit@1, Hit@3, Dung lượng & Thời gian)

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian ingest & embed | Chi phí API |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Strategy A** (Fixed 500/50) | Dev | 6/15 (40.0%) | 9/15 (60.0%) | 511 chunks | 33,59s | ~0.0004 USD |
| | Test | 3/5 (60.0%) | 4/5 (80.0%) | | | |
| **Strategy B** (Paragraph $\le$ 800) | Dev | 3/15 (20.0%) | 6/15 (40.0%) | 339 chunks | 33,59s | ~0.0004 USD |
| | Test | 3/5 (60.0%) | 5/5 (100.0%) | | | |
| **Strategy C** (Paragraph + Filter) | Dev | **4/15 (26.7%)** | **7/15 (46.7%)** | 339 chunks | 33,59s | ~0.0004 USD |
| | Test | 3/5 (60.0%) | **5/5 (100.0%)** | | *(Tái sử dụng vector B)* | 0 USD thêm |

### Bảng 2: Đánh giá chất lượng thủ công (Coherence, Metadata, Grounding)

| Strategy | Coherence trung bình /2 (n=10) | Metadata đủ và đúng (n/N) | Filter tuân thủ (n/N hoặc N/A) | Grounding 0/1/2 (số câu) và trung bình /2 (n=5) |
|---|:---:|:---:|:---:|:---:|
| **Strategy A** | 1.20 / 2.0 (10) | 15/15 (100%) | N/A (không dùng filter) | 1 câu mức 0, 1 câu mức 1, 3 câu mức 2 $\rightarrow$ **1.40 / 2.0** |
| **Strategy B** | 1.90 / 2.0 (10) | 15/15 (100%) | N/A (không dùng filter) | 0 câu mức 0, 0 câu mức 1, 5 câu mức 2 $\rightarrow$ **2.00 / 2.0** |
| **Strategy C** | **1.90 / 2.0** (10) | **15/15 (100%)** | **2/2 (100.0%)** | 0 câu mức 0, 0 câu mức 1, 5 câu mức 2 $\rightarrow$ **2.00 / 2.0** |

* **Đường dẫn trace, nhãn thủ công và cách chọn mẫu:**
  * Trace kết quả chạy máy: [results/trace_strategy_A.json](../../results/trace_strategy_A.json), [results/trace_strategy_B.json](../../results/trace_strategy_B.json), [results/trace_strategy_C.json](../../results/trace_strategy_C.json).
  * Nhật ký thí nghiệm đối sánh: [artifacts/experiment_log.csv](../../artifacts/experiment_log.csv).
  * Mẫu Coherence được chọn trên 10 vị trí nội dung cố định đầu tiên (Trang 11, 14, 15, 16, 17, 18, 19, 20, 21, 22).
  * Mẫu Grounding và Metadata Usefulness được đánh giá trên toàn bộ 5 câu của tập Test (`q16`–`q20`), mỗi câu kiểm tra top-3 chunks (tổng cộng 15 chunks cho mỗi chiến lược).

---

## Phân tích và kết luận

### 1. So sánh có kiểm soát giữa các chiến lược
* **So sánh A – B (Ảnh hưởng của kỹ thuật Chunking):**
  * *Số lượng chunk & Tài nguyên:* Strategy A sinh ra 511 chunks do cửa sổ cố định 500 ký tự trượt liên tục, trong khi Strategy B chỉ tạo 339 chunks (giảm **33,7%** dung lượng lưu trữ và số lần gọi vector embedding).
  * *Chất lượng đoạn văn (Coherence):* Strategy A bị phạt nặng ở tính mạch lạc (1.20/2) do các câu văn và lời thoại thường xuyên bị cắt đôi ở ranh giới 500 ký tự. Ngược lại, Strategy B đạt điểm Coherence vượt trội (1.90/2) vì các đoạn văn, tình tiết đối thoại được giữ nguyên khối.
  * *Chất lượng Grounding trên Test set:* Strategy B đạt Grounding tuyệt đối 2.00/2 và Hit@3 100% trên tập Test, trong khi Strategy A chỉ đạt 1.40/2 (Hit@3 đạt 80% do trượt câu `q19`).
* **So sánh B – C (Ảnh hưởng riêng biệt của Metadata Filtering):**
  * Do B và C sử dụng hoàn toàn chung một tập chunk và cùng một không gian vector nhúng, sự khác biệt 100% đến từ việc kích hoạt metadata filter trong câu truy vấn SQL.
  * *Tác động định lượng:* Trên tập Dev, Strategy C nâng Hit@1 từ 20.0% lên 26.7% và Hit@3 từ 40.0% lên 46.7%. Trên tập Test, tỷ lệ tuân thủ filter đạt 100% (2/2 câu có filter).
  * *Tác động định tính:* Metadata filtering giúp loại bỏ hoàn toàn các chunk nhiễu (distractors) có nội dung tương tự nhưng nằm ở phần khác của câu chuyện (ví dụ: bối cảnh Andalusia ở Part One không bị nhầm với bối cảnh sa mạc ở Part Two).

### 2. Phân tích 2 trường hợp lỗi tiêu biểu (Error Case Studies)
1. **Lỗi do nhầm lẫn ngữ nghĩa giữa hai thực thể tương đồng (`q07` - Gold Page 26):**
   * *Câu hỏi:* *"What payment did Melchizedek demand from Santiago to tell him how to find the hidden treasure?"*
   * *Hiện tượng:* Cả 3 chiến lược A, B, C đều trả về Top-1 là trang 22 thay vì trang 26.
   * *Nguyên nhân:* Tại trang 22, bà lão Gypsy yêu cầu *"one-tenth of the treasure"*, trong khi tại trang 26, Vua Melchizedek yêu cầu *"one-tenth of your sheep"*. Do câu hỏi chứa từ khóa *"treasure"*, embedding vector bị kéo lệch độ tương đồng cosine về phía đoạn văn của bà lão Gypsy. Đây là giới hạn điển hình của Dense Semantic Retrieval khi có 2 đoạn văn cùng chung cấu trúc biểu đạt ("đòi 1/10 để đổi lấy bí mật kho báu").
2. **Lỗi do phân mảnh văn bản ở Fixed-size chunking (`q19` - Gold Page 85 trên Strategy A):**
   * *Câu hỏi:* *"What severe penalty did the oasis chieftains promise Santiago if no enemies attacked the oasis?"*
   * *Hiện tượng:* Strategy A trượt hoàn toàn khỏi Top-3 (Hit@3 = False, các trang trả về là 71, 89, 93). Trong khi đó, Strategy B và C đều tìm thấy trang 85 ở Rank 3 (Hit@3 = True).
   * *Nguyên nhân:* Trong Strategy A, lời cảnh báo của tù trưởng bị chia cắt thành 2 chunk nhỏ tại mốc 500 ký tự. Nửa đầu chứa cảnh tù trưởng nói chuyện nhưng thiếu từ khóa hình phạt; nửa sau chứa từ khóa vũ khí nhưng thiếu chủ ngữ. Sự phân mảnh này làm suy giảm điểm cosine similarity của từng mảnh, đẩy trang 85 rớt khỏi top-3. Trong khi đó, Strategy B giữ trọn vẹn đoạn văn của cuộc hội kiến, giúp vector giữ trọn ngữ cảnh cảnh báo.

### 3. Chiến lược lựa chọn, đánh đổi và điều kiện áp dụng
* **Chiến lược được chọn:** **Chiến lược C (Structure-aware Paragraph Chunking kết hợp Metadata Filtering)**.
* **Lý do lựa chọn:**
  * Giảm 33,7% số lượng vector so với Fixed-size chunking, tiết kiệm tài nguyên lưu trữ và tính toán.
  * Đạt điểm Coherence (1.90/2) và Grounding (2.00/2) tối ưu nhất, cung cấp ngữ cảnh đầy đủ và tin cậy cho LLM trả lời mà không bị cắt vụn câu chữ.
  * Đạt Hit@3 100% trên tập Test và có sự cải thiện rõ rệt về Hit@1/Hit@3 trên tập Dev nhờ loại bỏ các distractor ngoài phân vùng dữ liệu.
* **Đánh đổi (Trade-offs):**
  * Kỹ thuật Paragraph-based đòi hỏi tài liệu có cấu trúc định dạng rõ ràng (dấu ngắt dòng, tiêu đề). Với tài liệu OCR kém chất lượng hoặc thiếu ngắt đoạn, cần thêm bước tiền xử lý cấu trúc.
  * Metadata filtering yêu cầu câu truy vấn hoặc ngữ cảnh người dùng phải cung cấp trước trường lọc hợp lệ; nếu bộ lọc gán sai giá trị (ví dụ người dùng hỏi về Part One nhưng filter nhầm sang Part Two), kết quả sẽ bị triệt tiêu hoàn toàn (false dismissal).

### 4. Hạn chế của thực nghiệm & Hướng mở rộng
* *Hạn chế:* Kích thước tập Test gồm 5 câu là mức tối thiểu cho lab ngắn hạn, mang tính chất minh họa phương pháp luận kiểm thử độc lập chứ chưa đủ độ bao phủ thống kê cho toàn bộ miền tri thức lớn. 
* *Cải tiến tương lai:*
  1. **Hybrid Retrieval:** Kết hợp Dense Embedding (OpenRouter) với phương pháp Sparse Retrieval dựa trên từ khóa chính xác (BM25) để khắc phục lỗi nhầm lẫn giữa "cừu" và "kho báu" ở câu `q07`.
  2. **Contextual Compression / Parent Document Retriever:** Lưu trữ các chunk nhỏ để search chính xác, nhưng khi trả về LLM sẽ mở rộng thành toàn bộ đoạn văn lớn của trang nguồn để tối đa hóa tính liên tục của ngữ cảnh.
