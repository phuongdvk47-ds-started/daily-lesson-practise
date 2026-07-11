# Post-Render PDF QC

## Role

Post-Render PDF QC checks the actual exported PDF, not just `lesson_source.json`.

It prevents cases where JSON is correct but PDF output is incomplete or inconsistent.

## Required Checks

### 1. Multiple Choice Options Rendering

For every Reading or Grammar question where:

```json
"type": "Multiple Choice",
"options": ["...", "...", "...", "..."]
```

The rendered PDF must contain:

* the question stem
* all options
* labels A/B/C/D or a clear option list

Fail if:

* options exist in JSON but are absent from PDF
* fewer options are rendered than expected
* option labels are missing and layout is ambiguous

### 2. Blank Preservation

For Grammar MCQ and gap-fill questions, the PDF must preserve blanks such as:

```text
_______
```

Fail if the blank disappears and the sentence becomes ungrammatical, for example:

```text
The cinema, was built in 1920...
```

### 3. Computed Grammar Ranges

Rendered Grammar section headings must not use stale hardcoded ranges.

Fail if PDF contains:

```text
questions 27–36
questions 37–46
questions 47–56
```

unless those ranges are actually correct.

Expected:

```text
Questions 14–23
Questions 24–33
Questions 34–43
```

or neutral headings:

```text
Part A. Multiple Choice Questions
Part B. Error Correction
Part C. Sentence Transformation and Combining
```

### 4. Time Allowed Consistency

The `Time Allowed` shown in PDF must equal `lesson_meta.printed_time_allowed_minutes`.

Fail if:

* PDF hardcodes 50 mins
* JSON says a different value
* estimated time and printed time differ by more than allowed threshold

### 5. Visual Data Rendering

For every writing task with:

```json
"visual_data": {
  "type": "svg"
}
```

The PDF must render the visual clearly.

Check:

* chart title visible
* axis labels visible
* category labels visible
* data labels visible
* visual fits page width

### 6. Writing Space

For every Writing task, verify sufficient answer space:

* 1 sentence: at least 1 line
* 3–4 sentences: at least 4 lines
* 3-sentence description: at least 4 lines
* 50–60 words: at least 5–7 lines
* data description: at least 4–6 lines

### 7. Footer and Metadata

Each page must include:

* Lesson ID
* Document Type
* Page Number

### 8. Warm-up Specificity

PDF warm-up questions must be topic-specific.

Fail if warm-up uses generic placeholders:

* What do you think about this topic?
* Share a real experience related to this topic.
* Why is this topic important in daily life?

## Output Format

Post-Render PDF QC must return:

```json
{
  "status": "pass | fail",
  "checked_pdf": "",
  "issues": [
    {
      "severity": "low | medium | high | critical",
      "section": "",
      "page": 1,
      "problem": "",
      "expected": "",
      "actual": "",
      "fix_scope": "template | exporter | lesson_json | content_agent"
    }
  ]
}
```

## Pass Rule

Post-Render PDF QC passes only if:

* no critical issues
* no high issues
* all required options are visible
* all grammar blanks are preserved
* section ranges are correct
* Time Allowed is consistent
* visual data renders correctly
* writing spaces are sufficient

### 9. Correct-the-Error PDF Rendering Checks
- Verify that every Correct-the-error item in the PDF displays the original erroneous sentence, not the corrected sentence.
- Verify that no Correct-the-error item is already correct in the PDF worksheet.
- Fail if any known regression strings appear (e.g. `Correct the error: Local businesses do not like...` or `Correct the error: This school is more expensive...`).

### 10. Visual Layout & Duplicate Checking
- Verify that SVG charts/graphs are not rendered twice.
- Verify that writing tasks do not contain duplicate label headers (like `Word Ordering: Word Ordering:`).
- Verify that Time Allowed matches the JSON and is a rounded standard value (45, 60, 75, 90, 105, 120).

