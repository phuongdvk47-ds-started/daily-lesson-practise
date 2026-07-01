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

#### B. Bộ tài liệu đầu ra (Deliverables)
Mỗi ngày học được lưu trữ trong thư mục `/outputs/ielts-daily-reading-writing/[Day]-[Level]/`:
* **Thư mục `/lsn/` (Tài liệu học sinh)**:
  1. `*-Practise.pdf`: Phiếu bài tập (Reading, Grammar, Writing).
  2. `*-Vocabulary-Grammar.pdf`: Phiếu học lý thuyết (Vocab table, Grammar guide, IELTS Traps).
  3. `*-Vocab-Checker.pdf`: Phiếu kiểm tra từ vựng ngẫu nhiên (điền từ tiếng Anh).
* **Thư mục `/aws/` (Đáp án và Chấm bài)**:
  4. `*-Answers.pdf`: Đáp án chi tiết giải thích tư duy từng bước bằng tiếng Việt.
  5. `*-Vocab-Checker-Answer.pdf`: Đáp án phiếu kiểm tra từ vựng (in chữ màu đỏ đậm).
* **Thư mục gốc ngày học**:
  6. `*-Quizlet-Vocab.md`: Tệp Markdown dùng để import vào Quizlet.
  7. `lesson_source.json`: Dữ liệu thô gốc của bài học.

#### C. Hướng dẫn sử dụng & Biên dịch (CLI Commands)

##### 1. Chạy xác thực dữ liệu JSON (Validate Payload):
Trước khi biên dịch ra PDF, chạy script validator để kiểm tra tính hợp lệ của schema, số lượng câu hỏi, và tính chính xác của trích dẫn chứng cứ đọc hiểu:
```powershell
python .agents/skills/ielts-daily-reading-writing/scripts/validate_lesson_json.py <path_to_json>
```
*Script trả về exit code 0 nếu hợp lệ, exit code 1 nếu phát hiện lỗi kèm danh sách lỗi chi tiết.*

##### 2. Biên dịch bài học hàng ngày ra PDF:
```powershell
uv run --with playwright python .agents/skills/ielts-daily-reading-writing/scripts/export_daily_pack.py <path_to_json> [--out-dir <output_path>]
```

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

#### D. Hướng dẫn viết Prompt kích hoạt AI (Prompting Guide)
Khi bạn muốn tạo một bài học luyện IELTS Daily mới, hãy sử dụng mẫu prompt dưới đây để ra lệnh cho AI. Hệ thống hỗ trợ nạp giá trị mặc định (defaults) tự động nếu bạn bỏ trống một số tham số.

##### Mẫu Prompt chuẩn kích hoạt AI (Prompt Template):
> Hãy tạo một bài luyện tập IELTS Daily Reading & Writing mới cho học sinh với các thông số sau:
> - **Level**: [Điền level, ví dụ: A2 | B1 | B2 | C1] (Mặc định: A2)
> - **Day**: [Điền ngày dạng YYYYMMDD, ví dụ: 20260701] (Mặc định: Ngày hôm nay)
> - **Topic**: [Điền tên chủ đề hoặc bỏ trống để AI tự chọn chủ đề chuẩn từ topic-bank.md]
> - **Reading Questions**: [Số lượng câu hỏi đọc hiểu, ví dụ: 13] (Mặc định: 13)
> - **Vocabulary Words**: [Số lượng từ vựng cần trích xuất, ví dụ: 20] (Mặc định: 20)
> - **Grammar Questions**: [Số lượng câu hỏi ngữ pháp, ví dụ: 30] (Mặc định: 30)
> - **Writing Practice**: [Số lượng task viết, ví dụ: 5] (Mặc định: 5)
> - **Source URL**: [Optional - Link bài đọc nguồn từ BBC/VOA nếu muốn chỉ định]
> 
> *Yêu cầu thêm*: Hãy đối chiếu file history để chống trùng lặp Theme/Topic, tìm bài học cùng level gần nhất trong history để recycle 3 từ vựng (spaced repetition), áp dụng quy tắc thiết kế câu hỏi đáp án duy nhất và chống Skimming/Scanning cho Reading. Xuất dữ liệu ra JSON phân rã theo output-schema.md.

##### Ví dụ Prompt thực tế ngắn gọn:
> Tạo bài luyện IELTS ngày 20260701, Level B2, chủ đề "Urban Environments", lấy nguồn từ một bài viết VOA Learning English hoặc BBC News. Trích xuất 20 từ vựng mới, recycle 3 từ từ bài B2 gần nhất, 30 câu hỏi ngữ pháp và 5 task viết (có biểu đồ SVG so sánh dữ liệu). Hãy thiết kế câu hỏi đọc hiểu paraphrase sâu chống skimming và có đáp án duy nhất.

---

## Kế hoạch Mở rộng các Skills Tương lai
Dự án được cấu trúc sẵn sàng để tích hợp thêm các môn học/kỹ năng mới:
* `### SAT Preparation (sat-preparation)`: Tự động tạo đề luyện thi SAT (Math & Verbal).
* `### Daily Mathematics (daily-mathematics)`: Bài tập toán học tư duy hàng ngày.
* `### IELTS Listening & Speaking (ielts-listening-speaking)`: Luyện tập phát âm và nghe hiểu tích hợp audio.
