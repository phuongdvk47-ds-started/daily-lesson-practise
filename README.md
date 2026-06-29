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
Kỹ năng tự động tạo đề luyện tập kỹ năng Đọc (Reading) và Viết (Writing) theo chuẩn IELTS học thuật từ cấp độ A1 đến C2. Hệ thống tự động trích xuất bảng từ vựng thông minh, bài học ngữ pháp bổ trợ, phiếu kiểm tra từ vựng ngẫu nhiên và bộ hướng dẫn giải chi tiết đóng vai trò là giáo viên hướng dẫn tư duy.

#### A. Bộ tài liệu đầu ra (Deliverables)
Mỗi ngày học được lưu trữ trong thư mục `/outputs/ielts-daily-reading-writing/[Day]-[Level]/` bao gồm 5 tệp PDF học tập (chia làm 2 thư mục con), 1 tệp Quizlet Markdown và 1 tệp JSON gốc:
* Thư mục con `/lsn/` (Tài liệu học sinh):
  1. **`*-Practise.pdf`**: Phiếu bài tập của học sinh (gồm câu hỏi đọc, ngữ pháp và viết).
  2. **`*-Vocabulary-Grammar.pdf`**: Phiếu học lý thuyết (Bảng từ vựng, phân loại từ, lý thuyết ngữ pháp, bảng bẫy lỗi thường gặp trong IELTS).
  3. **`*-Vocab-Checker.pdf`**: Phiếu kiểm tra từ vựng ngẫu nhiên (chỉ có nghĩa tiếng Việt và định nghĩa, bỏ trống từ tiếng Anh).
* Thư mục con `/aws/` (Đáp án cho giáo viên):
  4. **`*-Answers.pdf`**: Tệp đáp án chi tiết giải thích tư duy từng bước bằng tiếng Việt.
  5. **`*-Vocab-Checker-Answer.pdf`**: Đáp án của phiếu kiểm tra từ vựng.
* Thư mục gốc `/outputs/ielts-daily-reading-writing/[Day]-[Level]/`:
  6. **`*-Quizlet-Vocab.md`**: Tệp Markdown dùng để import vào Quizlet.
  7. **`lesson_source.json`**: Tệp dữ liệu thô gốc của bài học.

#### B. Hướng dẫn Biên dịch (CLI Commands)

##### Chạy biên dịch bài học hàng ngày:
```powershell
uv run --with playwright python .agents/skills/ielts-daily-reading-writing/scripts/export_daily_pack.py <path_to_input_json> [--out-dir <output_path>]
```

##### Tạo đề ôn tập lũy kế (Cumulative Review Pack):
Giúp tổng hợp từ vựng và ngữ pháp của nhiều ngày học cũ (ví dụ 1 tuần hoặc 2 tuần) để tạo thành một đề kiểm tra tổng hợp 120 phút.

* **Bước 1: Trích xuất và gom dữ liệu từ các bài cũ**:
  Lệnh này sẽ quét các thư mục bài học trong quá khứ để gom từ vựng và chủ điểm ngữ pháp:
  ```powershell
  python .agents/skills/ielts-daily-reading-writing/scripts/prepare_review_inputs.py --level B2 --days 20260625,20260626 > review_payload.json
  ```
  *(Nếu không truyền tham số `--days`, hệ thống tự động lấy 5 ngày gần nhất của level đó trong lịch sử).*

* **Bước 2: Biên dịch đề ôn tập ra PDF**:
  ```powershell
  uv run --with playwright python .agents/skills/ielts-daily-reading-writing/scripts/export_review_pack.py review_payload.json
  ```

#### C. Nguyên tắc Bảo tồn Nội dung (Content Consistency)
Khi nâng cấp hoặc cập nhật định dạng, footer, hoặc sinh thêm tệp phụ cho các bài học đã in ra cho học sinh làm:
1. **KHÔNG chạy lại AI** để tránh làm biến đổi nội dung bài đọc, câu hỏi hay đáp án cũ.
2. Chạy trực tiếp script biên dịch Python trỏ vào tệp **`lesson_source.json`** trong thư mục bài học đó:
   ```powershell
   uv run --with playwright python .agents/skills/ielts-daily-reading-writing/scripts/export_daily_pack.py outputs/ielts-daily-reading-writing/20260626-B2/lesson_source.json
   ```
   *Hệ thống sẽ tái bản toàn bộ file HTML và PDF theo định dạng mới nhưng giữ nguyên 100% nội dung chữ gốc.*

---

## Kế hoạch Mở rộng các Skills Tương lai
Dự án được cấu trúc sẵn sàng để tích hợp thêm các môn học/kỹ năng mới:
* `### SAT Preparation (sat-preparation)`: Tự động tạo đề luyện thi SAT (Math & Verbal).
* `### Daily Mathematics (daily-mathematics)`: Bài tập toán học tư duy hàng ngày.
* `### IELTS Listening & Speaking (ielts-listening-speaking)`: Luyện tập phát âm và nghe hiểu tích hợp audio.
