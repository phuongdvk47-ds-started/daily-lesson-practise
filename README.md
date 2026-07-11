# Daily Lesson Practice System

Hệ thống tự động sinh đề và quản lý tài liệu luyện tập hàng ngày dành cho giáo viên và học sinh. Dự án được thiết kế với cấu trúc module hóa (Agent Skills), cho phép mở rộng linh hoạt thêm nhiều môn học và kỹ năng khác nhau trong tương lai.

---

## Cấu trúc Dự án (Project Structure)
* `.agents/skills/`: Chứa các module kỹ năng (Skill) của hệ thống. Mỗi môn học/kỹ năng là một thư mục riêng biệt chứa hướng dẫn vận hành, các scripts Python biên dịch và các tệp mẫu HTML/CSS.
* `outputs/`: Thư mục lưu trữ tài liệu đầu ra sau khi biên dịch (HTML, PDF, Markdown).
* `lesson_history.txt`: Nhật ký ghi lại lịch sử các bài học đã sinh để chống trùng lặp.

---

## Danh sách Agent Skills Hiện Có

### 1. IELTS Daily Reading & Writing (`ielts-daily-reading-writing`)
Module tự động tạo đề luyện tập Đọc (Reading) và Viết (Writing) theo chuẩn IELTS học thuật từ cấp độ A1 đến C2. 

#### A. Kiến trúc Modular Pipeline mới
Skill được thiết kế theo mô hình pipeline chia nhỏ trách nhiệm (Sub-Agents) nhằm tối ưu hóa lượng token sử dụng, giảm thiểu tối đa hiện tượng ảo giác (hallucination) và nâng cao chất lượng học liệu:
1. **Source Research Agent**: Agent duy nhất có quyền tìm kiếm và xác thực nguồn bài đọc thực tế (VOA, BBC, British Council).
2. **Reading Agent**: Tạo bài đọc đếm từ chuẩn CEFR, tự động bold từ vựng mới và từ vựng recycled `[R]`, sinh câu hỏi đọc hiểu chống Skimming/Scanning và đảm bảo **đáp án là duy nhất**.
3. **Vocabulary Agent**: Trích xuất từ vựng (5 cột), định dạng Quizlet (Section 1 & 2) và ngẫu nhiên hóa phiếu Vocab Checker.
4. **Grammar Agent**: Biên soạn hướng dẫn ngữ pháp (dạng visual cards), bảng bẫy lỗi IELTS (IELTS Traps) và các câu hỏi ngữ pháp (đáp án duy nhất, đánh số liên tục từ 1).
5. **Writing Agent**: Sinh đề bài viết IELTS Task 1/2 tích hợp biểu đồ vector SVG, bảng dữ liệu và chừa các dòng kẻ viết `.writing-line` rộng rãi.
6. **Answer Agent**: Giáo viên giải thích bằng tiếng Việt chi tiết (Tóm tắt bài đọc, Câu X, Bằng chứng (§), Cách tìm đáp án, Mẹo thi và bài tập Review Bridge).
7. **Quality Control Agent**: Kiểm duyệt tự động độ khớp của counts, từ vựng ôn tập và tính chính xác của evidence quote so với bài đọc trước khi biên dịch.

Mọi dữ liệu sinh ra được gom về tệp **`lesson_source.json`** - đại diện cho **Single Source of Truth** trước khi biên dịch PDF.

#### B. Cơ chế Phản biện & Duyệt kết quả (Review Loop & HIL Checkpoints)
Skill hỗ trợ vòng phản biện tự động giữa các Sub-Agents (Agent Review Loop) và can thiệp phê duyệt của người dùng (Human-in-the-loop):
* **Chế độ tự động (Auto Mode - Mặc định)**: Các Sub-Agents tự kiểm duyệt chéo, QC Agent tự sinh challenge để sửa đổi cục bộ, và chỉ xuất PDF khi QC đạt trạng thái Pass. Không ngắt quãng người dùng.
* **Chế độ kiểm duyệt (Review Mode)**: Hệ thống tạm dừng tại 7 checkpoints cốt lõi để chờ người dùng duyệt hoặc chỉ đạo sửa đổi:
  1. *Source Approval*: Duyệt nguồn bài đọc.
  2. *Blueprint Approval*: Duyệt khung giáo án (chủ đề, mục tiêu từ vựng/ngữ pháp).
  3. *Reading Question Approval*: Duyệt bộ câu hỏi đọc hiểu.
  4. *Vocabulary Approval*: Duyệt bảng từ vựng và Quizlet.
  5. *Grammar Approval*: Duyệt lý thuyết và bài tập ngữ pháp.
  6. *Writing Task Approval*: Duyệt đề viết và biểu đồ SVG.
  7. *Pre-PDF Approval*: Duyệt chốt trước khi Playwright in ra PDF.

#### C. Bộ tài liệu đầu ra (Deliverables)
Mỗi ngày học được lưu trữ trong thư mục `/outputs/ielts-daily-reading-writing/[Day]-[Level]/`:
* **Thư mục `/lsn/` (Tài liệu học sinh)**:
  1. `*-Practise.pdf`: Phiếu bài tập (Reading, Grammar, Writing).
  2. `*-Vocabulary-Grammar.pdf`: Phiếu học lý thuyết (Vocab table, Grammar guide, IELTS Traps).
  3. `*-Vocab-Checker.pdf`: Phiếu kiểm tra từ vựng ngẫu nhiên (chừa trống từ tiếng Anh).
* **Thư mục `/aws/` (Đáp án và Chấm bài)**:
  4. `*-Answers.pdf`: Đáp án chi tiết giải thích tư duy từng bước bằng tiếng Việt.
  5. `*-Vocab-Checker-Answer.pdf`: Đáp án phiếu kiểm tra từ vựng (in chữ màu đỏ đậm).
* **Thư mục gốc ngày học**:
  6. `*-Quizlet-Vocab.md`: Tệp Markdown dùng để import vào Quizlet.
  7. `lesson_source.json`: Dữ liệu thô gốc của bài học (chứa cả log phản biện chéo và quyết định của người dùng).

#### D. Hướng dẫn sử dụng & Biên dịch (CLI Commands)

##### 1. Chạy xác thực dữ liệu JSON (Validate Payload):
Trước khi biên dịch ra PDF, chạy script validator để kiểm tra tính hợp lệ của schema, các open challenges, checkpoints, và giới hạn revision:
```powershell
python .agents/skills/ielts-daily-reading-writing/scripts/validate_lesson_json.py <path_to_json>
```
*Script trả về exit code 0 nếu hợp lệ, exit code 1 nếu phát hiện lỗi (ví dụ còn open challenge nghiêm trọng).*

##### 2. Biên dịch bài học hàng ngày ra PDF:
```powershell
uv run --with playwright python .agents/skills/ielts-daily-reading-writing/scripts/export_daily_pack.py <path_to_json> [--out-dir <output_path>]
```
*Chốt chặn an toàn (Safety Guardrails) tích hợp trong exporter sẽ từ chối xuất PDF nếu tệp JSON chưa được QC Pass hoặc còn open challenge mức High/Critical.*

##### 3. Tạo đề ôn tập lũy kế (Cumulative Review Pack):
* **Bước 1: Trích xuất và gom dữ liệu từ các bài cũ**:
  ```powershell
  python .agents/skills/ielts-daily-reading-writing/scripts/prepare_review_inputs.py --level B2 --days 20260625,20260626 > review_payload.json
  ```
* **Bước 2: Biên dịch đề ôn tập ra PDF**:
  ```powershell
  uv run --with playwright python .agents/skills/ielts-daily-reading-writing/scripts/export_review_pack.py review_payload.json
  ```

##### 4. Nguyên tắc Bảo tồn Nội dung (Content Consistency):
Khi muốn cập nhật lại thiết kế PDF (thay đổi CSS, footer, line-spacing), **tuyệt đối KHÔNG chạy lại AI**. Hãy chạy trực tiếp script biên dịch trỏ vào tệp `lesson_source.json` cũ để tái bản PDF mà không thay đổi một chữ nội dung nào:
```powershell
uv run --with playwright python .agents/skills/ielts-daily-reading-writing/scripts/export_daily_pack.py outputs/ielts-daily-reading-writing/20260626-B2/lesson_source.json
```

#### E. Hướng dẫn viết Prompt kích hoạt AI (Prompting Guide)
Khi bạn muốn tạo một bài học luyện IELTS Daily mới, hãy sử dụng các mẫu prompt ngắn gọn dưới đây để ra lệnh cho AI. Hệ thống sẽ tự động đối chiếu lịch sử, tự chọn chủ đề cấp độ tương ứng và nạp các giá trị mặc định khác.

##### Mẫu 1: Chạy Tự động (Auto Mode - Khuyên dùng)
> Hãy tạo đề luyện IELTS mới cho ngày **20260702**:
> - **Reading & Grammar**: Level **B1**
> - **Writing**: Level **A1**
> 
> *Yêu cầu*: Chạy Auto Mode. Các Sub-Agents tự động review chéo, QC Agent tự sinh challenge để sửa đổi cục bộ, và chỉ xuất PDF khi QC đạt trạng thái Pass.

##### Mẫu 2: Duyệt từng chặng (Review Mode)
> Hãy tạo đề luyện IELTS mới cho ngày **20260702** theo **Review Mode**:
> - **Reading & Grammar**: Level **B1**
> - **Writing**: Level **A1**
> 
> *Yêu cầu*: Hãy dừng lại để tôi duyệt tại các checkpoints: Nguồn bài đọc, Blueprint giáo án, và Chốt duyệt in PDF (Pre-PDF Approval).

### 2. IELTS Barron Essential Vocab (`ielts-baron-essential-vocab`)
Module tự động tạo các tập tài liệu luyện tập từ vựng, ngữ pháp, đọc hiểu chuẩn IELTS và hướng dẫn đáp án chi tiết từ nguồn sách Barron PDF hoặc các tài liệu nguồn khác. Module hoạt động dựa trên cơ chế pipeline có bộ đệm (cached), phân mảnh nhiệm vụ giữa các tiểu tác nhân (modular sub-agents), kết hợp kiểm duyệt của con người (HITL).

#### A. Kiến trúc Modular Cached Pipeline
Skill này được thiết kế dưới dạng một pipeline gồm 19 giai đoạn độc lập (từ Agent 00 đến Agent 18) nhằm tối ưu hóa tokens và tài nguyên xử lý:
* **Orchestrator Control Plane**: Đóng vai trò điều phối, phân phối các tác vụ, kiểm tra tính hợp lệ của dữ liệu đầu vào/đầu ra qua từng chặng nhưng không trực tiếp biên soạn hay trích xuất nội dung.
* **Mô hình thực thi linh hoạt (Execution Model)**: Tối ưu chi phí bằng nguyên tắc Ưu tiên Deterministic & Local trước, sau đó đến LLM giá rẻ, LLM cao cấp và cuối cùng là Con người duyệt:
  `DETERMINISTIC → LOCAL_MODEL → LOW_COST_LLM → PREMIUM_LLM → HUMAN_REQUIRED`
* **Cơ chế Cache-First**: Tự động bỏ qua các giai đoạn đã hoàn thành trước đó nếu tệp đầu ra tồn tại, khớp checksum đầu vào, schema hợp lệ và trạng thái ghi nhận là `COMPLETE`. Bộ đệm lưu tại `.cache/ielts-baron-essential-vocab/[unique_source_id]/`.

#### B. Cơ chế Chống ảo giác & Xác thực nguồn gốc (Anti-Hallucination & Provenance)
Mọi khối nội dung được tạo ra đều bắt buộc phải mang nhãn phân loại nguồn gốc rõ ràng (như `SOURCE_EXTRACTED`, `DERIVED_FROM_SOURCE`, `MODEL_GENERATED_DRAFT`, v.v.). Các thông tin trích dẫn nguồn gốc yêu cầu phải có đầy đủ: `source_id`, số trang (`page`), `block_id` và độ tin cậy trích xuất để đảm bảo tính xác thực tuyệt đối, nói không với việc tự ý tạo ra IPA, định nghĩa hoặc đáp án giả mạo.

#### C. Điểm kiểm duyệt của Người dùng (HITL Checkpoints)
Hệ thống tạm dừng tại 6 điểm chốt chính để chờ phản hồi từ người dùng (nếu bật chế độ `--human-review`):
1. **Checkpoint A (Source Selection)**: Chọn nguồn file hoặc thư mục.
2. **Checkpoint B (Unit Confirmation)**: Xác nhận Unit và phạm vi trang sách/chủ đề.
3. **Checkpoint C (Extraction Review)**: Kiểm tra kết quả OCR hoặc trích xuất văn bản bị lỗi.
4. **Checkpoint D (Level Approval)**: Phê duyệt cấp độ CEFR/IELTS Band được đánh giá.
5. **Checkpoint E (Content Preview)**: Xem trước dàn ý và nội dung tài liệu trước khi dựng khung.
6. **Checkpoint F (Final PDF Approval)**: Duyệt chốt các tệp PDF đã render.

#### D. Bộ tài liệu đầu ra (Deliverables)
Kết quả đầu ra lưu tại `outputs/ielts-baron-essential-vocab/[lesson_id]/`:
* `daily-practice.pdf`: Phiếu bài tập luyện tập từ vựng & đọc hiểu hàng ngày.
* `vocabulary-grammar.pdf`: Tài liệu lý thuyết từ vựng & ngữ pháp đi kèm.
* `answer-key.pdf`: Hướng dẫn đáp án chi tiết giải thích rõ ràng lý do chọn lựa.
* `complete-booklet.pdf` (*tùy chọn*): Sách bài tập tích hợp hoàn chỉnh.
* `lesson-manifest.json`, `provenance-report.json`, `qa-report.json`: Các tệp siêu dữ liệu, báo cáo nguồn gốc và kết quả kiểm soát chất lượng.
* Thư mục `render/html/`: Mã nguồn HTML/CSS dùng để tạo PDF.

#### E. Hướng dẫn sử dụng & Biên dịch (CLI Commands)

##### 1. Chạy toàn bộ pipeline tạo bài học mới:
```powershell
python scripts/run_pipeline.py --source "<path-or-url>" --unit "Unit 1" --topic "Bird Migration" --day 1 --human-review
```

##### 2. Chỉ biên dịch/render lại giao diện (không chạy lại AI trích xuất):
```powershell
python scripts/run_pipeline.py --lesson-id "LSN-001-B2-A7K9P2QX" --from-stage html-render --force-rerender
```

##### 3. Quét OCR lại một trang cụ thể (phục vụ sửa đổi cục bộ):
```powershell
python scripts/run_pipeline.py --source "<source>" --from-stage extract --page 18 --force-page-reextract
```

##### 4. Khôi phục và tiếp tục chạy pipeline từ điểm lỗi gần nhất:
```powershell
python scripts/run_pipeline.py --resume --lesson-id "LSN-001-B2-A7K9P2QX"
```

---

## Kế hoạch Mở rộng các Skills Tương lai
Dự án được cấu trúc sẵn sàng để tích hợp thêm các môn học/kỹ năng mới:
* `### SAT Preparation (sat-preparation)`: Tự động tạo đề luyện thi SAT (Math & Verbal).
* `### Daily Mathematics (daily-mathematics)`: Bài tập toán học tư duy hàng ngày.
* `### IELTS Listening & Speaking (ielts-listening-speaking)`: Luyện tập phát âm và nghe hiểu tích hợp audio.
