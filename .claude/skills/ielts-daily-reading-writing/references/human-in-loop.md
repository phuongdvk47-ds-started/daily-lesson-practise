# Human-in-the-loop Workflow

## Role
Human-in-the-loop allows the user to review and approve important stages before the final PDF is exported.

The workflow must support two modes:
- Auto Mode
- Review Mode

## 1. Auto Mode
Use Auto Mode by default.
In Auto Mode, do not stop for user approval unless:
- Source verification is uncertain.
- Multiple source candidates are close in quality.
- Topic difficulty is mismatched with the requested level.
- QC fails after the maximum allowed revision attempts.
- The user explicitly requested human approval.

Auto Mode must still run internal Agent Review Loop and QC Challenge Loop.

## 2. Review Mode
Use Review Mode when the user says any of the following:
- "cho tôi duyệt nguồn trước"
- "review từng phần"
- "dừng trước khi export PDF"
- "cho tôi kiểm tra câu hỏi"
- "cho tôi duyệt vocabulary"
- "chạy human-in-loop"
- "manual approval"
- "review mode"
- "tôi muốn duyệt trước"

## 3. Human Checkpoints
The Skill must support these checkpoints:

### Checkpoint 1: Source Approval
Trigger:
- User asks to approve source.
- Source confidence is low.
- Multiple good source candidates exist.
- Source is copyrighted and only partial excerpt can be used.

Show:
- Source title
- Publisher
- URL
- Credibility note
- Relevance note
- Copyright note
- Proposed use

Ask:
"Bạn duyệt nguồn này để tạo Reading không?"

Allowed human actions:
- approve
- reject
- choose another source
- provide own source URL
- change topic
- continue in Auto Mode

### Checkpoint 2: Lesson Blueprint Approval
Trigger:
- User asks to review lesson plan.
- Topic/level mismatch is detected.
- New curriculum route is selected.

Show:
- Day
- Level by section
- Topic
- Reading source
- Grammar targets
- Vocabulary mix plan
- Writing task plan
- Stretch ratio

Ask:
"Bạn duyệt blueprint này để tạo nội dung chi tiết không?"

Allowed human actions:
- approve
- adjust topic
- adjust grammar target
- adjust writing level
- adjust question counts
- adjust stretch ratio

### Checkpoint 3: Reading Question Approval
Trigger:
- User asks to review Reading.
- QC flags Reading quality.
- Reading questions contain many stretch items.

Show compact table:
- Question ID
- Type
- Skill tested
- Correct answer
- Evidence paragraph
- QC note

Ask:
"Bạn duyệt bộ câu hỏi Reading này không?"

Allowed human actions:
- approve
- ask to make easier
- ask to make harder
- ask to reduce scanning
- ask to regenerate specific questions

### Checkpoint 4: Vocabulary Approval
Trigger:
- User asks to review vocabulary.
- Vocabulary mix is imbalanced.
- Too many single words.
- Idioms are questionable for the level.

Show:
- Count by vocab_type
- Sample items
- Recycled vocabulary
- Writing-useful chunks

Ask:
"Bạn duyệt danh sách từ vựng này không?"

Allowed human actions:
- approve
- add more phrases
- add more idioms
- remove idioms
- add more academic vocabulary
- make vocabulary easier
- make vocabulary harder

### Checkpoint 5: Grammar Approval
Trigger:
- User asks to review Grammar.
- QC flags ambiguity or multiple answers.
- Grammar level mismatch exists.

Show:
- Grammar targets
- Question type distribution
- Stretch items
- Ambiguity warnings if any

Ask:
"Bạn duyệt phần Grammar này không?"

Allowed human actions:
- approve
- change grammar target
- make easier/harder
- regenerate ambiguous questions
- add more transformation/combine/correct questions

### Checkpoint 6: Writing Task Approval
Trigger:
- User asks to review Writing.
- Writing contains visual data.
- Writing level differs from Reading/Grammar level.

Show:
- Writing task list
- Target length
- Visual data type
- Grammar/vocabulary focus
- Success criteria

Ask:
"Bạn duyệt Writing tasks này không?"

Allowed human actions:
- approve
- change task type
- add chart/table/map
- make more IELTS-like
- make more scaffolded
- change writing level

### Checkpoint 7: Pre-PDF Approval
Trigger:
- User asks to review before PDF.
- QC passes but layout risk exists.
- The pack is very long.

Show:
- QC result
- Counts
- Output files to be generated
- Any layout warnings

Ask:
"QC đã pass. Bạn có muốn export PDF không?"

Allowed human actions:
- approve export
- revise section
- export only selected files
- stop after JSON

## 4. Human Decision Log
Every human decision must be recorded in `lesson_source.json`:
```json
{
  "human_review": {
    "mode": "auto | review",
    "checkpoints": [
      {
        "checkpoint": "source_approval",
        "status": "approved | rejected | revised | skipped",
        "user_instruction": "",
        "decision_time": "",
        "affected_sections": []
      }
    ]
  }
}
```

## 5. Default Behavior
If the user does not explicitly request Review Mode:
- Run Auto Mode.
- Do not interrupt the workflow.
- Still run QC Challenge Loop.
- Return final QC report and generated files.

If QC fails repeatedly:
- Stop.
- Show the unresolved issues.
- Ask the user for direction.
