# Output JSON Schema — Field Reference

This document defines the required fields of `lesson_source.json` in a compact format for LLM guidance.
The **full formal JSON Schema (draft-07)** is in `output-schema-full.md`.
Runtime validation is done by `scripts/validate_lesson_json.py` which uses `output-schema-full.md`.

## Top-Level Required Keys
`execution` · `human_review` · `agent_review` · `lesson_meta` · `source` · `reading` · `vocabulary` · `grammar` · `writing` · `answers` · `warm_up`

---

## `execution`
| Field | Type | Values |
|---|---|---|
| `mode` | string | `auto` \| `review` |
| `pipeline_status` | string | `draft` \| `reviewing` \| `qc_failed` \| `qc_passed` \| `exported` |
| `current_stage` | string | free text |
| `revision_attempts` | object | keys: `source` `reading` `vocabulary` `grammar` `writing` `answers` `pdf_layout` (all integers) |

---

## `human_review`
| Field | Type | Notes |
|---|---|---|
| `mode` | string | `auto` \| `review` |
| `checkpoints` | array | Each item: `checkpoint` (str), `status` (`approved`\|`rejected`\|`revised`\|`skipped`), `user_instruction` (str), `decision_time` (str), `affected_sections` (str[]) |

---

## `agent_review`
| Field | Type | Notes |
|---|---|---|
| `reviews` | array | Each item: `reviewer_agent`, `reviewed_section`, `review_status` (`pass`\|`challenge`), `strengths` (str[]), `challenges` (str[]) |
| `challenges` | array | See **Challenge Object** below |

### Challenge Object (required fields)
`id` · `from_agent` · `to_agent` · `challenge_type` (see enum below) · `severity` (`low`\|`medium`\|`high`\|`critical`) · `location` · `problem` · `required_fix` · `status` (`open`\|`resolved`\|`accepted_by_user`\|`rejected`) · `revision_attempt` (int)

### `challenge_type` Enum
`source_quality` · `level_mismatch` · `ambiguity` · `multiple_answers` · `multiple_valid_answers` · `missing_evidence` · `insufficient_context` · `weak_distractor` · `keyword_scanning` · `vocabulary_imbalance` · `missing_vocab_type` · `grammar_target_mismatch` · `grammar_pattern_repetition` · `surface_clue_only` · `cognitive_level_imbalance` · `missing_deep_grammar_validation` · `missing_blueprint` · `blueprint_mismatch` · `logic_error` · `incomplete_punctuation` · `incomplete_inserted_option` · `missing_error_in_error_correction` · `answer_identical_to_prompt` · `explanation_mismatch` · `writing_visual_missing` · `answer_explanation_weak` · `pdf_layout_risk` · `schema_error` · `human_preference_required` · `numbering_error` · `meaning_changed` · `topic_alignment` · `time_workload_mismatch` · `reading_order_violation`

---

## `lesson_meta`
| Field | Type | Notes |
|---|---|---|
| `lesson_id` | string | Format: `LSN-[Day]-[Level]-[Random8]` |
| `day` | string | `YYYYMMDD` |
| `level` | string | `A1`\|`A1+`\|`A2`\|`A2+`\|`B1`\|`B1+`\|`B2`\|`B2+`\|`C1`\|`C1+`\|`C2` |
| `theme` | string | |
| `topic` | string | |
| `specific_topic` | string | |
| `created_at` | string | ISO datetime |
| `reading_question_count` | int | |
| `vocabulary_count` | int | |
| `grammar_question_count` | int | |
| `writing_task_count` | int | |
| `printed_time_allowed_minutes` | int | Standard classroom value: 45/60/75/90/105/120 |
| `estimated_completion_time_minutes` | int | |
| `time_workload_status` | string | `ok`\|`warning`\|`mismatch` |

---

## `source`
Required: `status` · `source_title` · `publisher` · `verified_url`
Optional: `author` · `published_date` · `access_date` · `url_status` · `credibility_note` · `topic_relevance_note` · `usable_excerpt` · `copyright_note` · `failure_reason`
`status`: `verified` | `failed`

---

## `reading`

### `reading_blueprint` (array, one item per question)
Each item: `question_no` (int) · `type` (str) · `depth` (`low`\|`medium`\|`high`) · `target_skill` (str) · `evidence_strategy` (`single sentence`\|`multiple sentences`\|`paragraph-level`\|`cross-paragraph`) · `distractor_strategy` (str)

### `passage`
`title` (str) · `paragraphs` (array of `{id: int, text: str}`)

### `questions` (array)
Required per item:
| Field | Type | Notes |
|---|---|---|
| `id` | int | |
| `type` | string | |
| `question` | string | |
| `options` | str[] | empty for TFNG/gap-fill |
| `correct_answer` | string | |
| `evidence_paragraph` | int | index into paragraphs |
| `evidence_quote` | string | verbatim from passage |
| `rationale_vi` | string | Vietnamese reasoning |
| `reasoning_skill` | string | `literal`\|`paraphrase`\|`inference`\|`reference`\|`main_idea`\|`author_purpose`\|`structure_function`\|`vocabulary_in_context`\|`synthesis`\|`comparison`\|`cause_effect`\|`contrast`\|`classification`\|`writer_purpose` |
| `source_scope` | string | always `"printed_passage_only"` |
| `stretch` | bool | |
| `paraphrase_mapping` | string | required for non-literal questions |
| `keyword_overlap_check` | string | |
| `distractor_analysis` | array | Each: `option` (str), `is_keyword_trap` (bool), `analysis` (str) |

---

## `vocabulary`

### `items` (array, count = vocabulary_count)
Each: `id`(int) · `term`(str) · `ipa`(str) · `part_of_speech`(str) · `definition_en`(str) · `meaning_vi`(str) · `example`(str) · `vocab_type` (`single_word`\|`phrase`\|`idiom`\|`fixed_expression`\|`collocation`\|`topic_vocabulary`\|`academic_vocabulary`) · `source` (`reading`\|`topic-extension`)

### `recycled_items` (array, exactly 3)
Each: `term` · `ipa` · `part_of_speech` · `meaning_vi` · `source_day`

### `quizlet`
`section_1_simple` (str[]) · `section_2_detailed` (str[])

### `vocab_checker_items` (array)
Each: `term` · `ipa` · `part_of_speech` · `definition_en` · `meaning_vi`

---

## `grammar`

### `grammar_blueprint` (array, one item per question)
Each: `question_no`(int) · `grammar_target`(str) · `question_type` (`controlled choice`\|`contextual choice`\|`error correction`\|`transformation`\|`paragraph editing`\|`writing transfer`) · `depth`(`low`\|`medium`\|`high`) · `tested_dimension`(str) · `trap`(str)

### `targets` (array)
Each: `name`(str) · `level`(str) · `reason`(str)

### `guide` (array)
Each: `heading`(str) · `content`(str)

### `common_mistakes` (array)
Each: `trap`(str) · `wrong_example`(str) · `correct_version`(str) · `why_it_matters`(str)

### `sections` (array)
Each: `section_title`(str) · `internal_question_start`(int) · `internal_question_end`(int) · `display_question_start`(int\|null) · `display_question_end`(int\|null) · `compiler_computed_range`(bool)

### `questions` (array)
Required per item:
| Field | Type | Notes |
|---|---|---|
| `id` | int | starts at 1 |
| `type` | string | |
| `question` | string | |
| `options` | str[] | empty for gap-fill/transform |
| `correct_answer` | string | |
| `explanation_vi` | string | |
| `difficulty` | string | `easy`\|`medium`\|`hard` |
| `cognitive_level` | string | `form_recognition`\|`context_use`\|`meaning_preservation`\|`editing_accuracy`\|`writing_transfer`\|`register_control`\|`precision_editing` |
| `source_connection` | string | `reading_based`\|`writing_transfer`\|`independent` |
| `target_structure` | string | |
| `level` | string | CEFR level |
| `stretch` | bool | |
| `one_answer_check` | object | see below |
| `deep_grammar_validation` | object | see below |

### `one_answer_check` (required fields)
`has_exactly_one_valid_answer`(bool) · `context_is_sufficient`(bool) · `final_sentence_after_insertion`(str) · `why_correct_is_unique`(str) · `why_other_options_are_wrong`(array of `{option, reason}`) · `punctuation_complete`(bool) · `meaning_preserved`(bool) · `target_structure_clear`(bool) · `answer_family_is_bounded`(bool)

### `deep_grammar_validation` (required fields)
`has_single_clear_answer`(bool) · `requires_context_or_meaning`(bool) · `meaning_preserved_if_transformation`(bool) · `is_not_surface_clue_only`(bool) · `matches_target_structure`(bool) · `difficulty_is_appropriate`(bool) · `level_is_appropriate`(bool)

### `option_validations` (MCQ questions only)
Array of `{option(str), is_correct(bool), why_wrong(str)}`

### `meaning_preservation_validation` (transformation/combine questions)
`original_meaning`(str) · `transformed_meaning`(str) · `meaning_is_preserved`(bool) · `target_structure_used`(bool) · `no_extra_information_added`(bool) · `no_information_removed`(bool) · `answer_family_is_narrow`(bool)

### `error_correction_validation` (error correction questions)
`original_sentence`(str) · `corrected_sentence`(str) · `target_error_text`(str) · `target_error_type`(str) · `correction_text`(str) · `original_contains_error`(bool) · `corrected_differs_from_original`(bool) · `exactly_one_target_error`(bool) · `explanation_matches_error`(bool)

---

## `writing`

### `tasks` (array, count = writing_task_count)
Each: `id`(int) · `task_type`(str) · `prompt`(str) · `target_length`(str) · `focus_skill`(str) · `useful_language`(str[]) · `success_criteria`(str[]) · `visual_data`(`{type: "none"|"markdown_table"|"svg", content: str}`) · `topic_alignment`(bool)

**Critical**: `useful_language` and `success_criteria` must be **arrays of strings**, not comma-separated strings.

---

## `answers`

### `reading_answers` (array)
Each: `question_id`(int) · `correct_answer`(str) · `question_type`(str) · `evidence_quote`(str) · `evidence_paragraph`(int) · `explanation_vi`(str) · `why_others_wrong_vi`(str) · `depth_check_vi`(str) · `tip_vi`(str) · `stretch_note`(str)

### `grammar_answers` (array)
Each: `question_id`(int) · `correct_answer`(str) · `grammar_target`(str) · `form_meaning_vi`(str) · `use_in_context_vi`(str) · `trap_logic_vi`(str) · `why_others_wrong_vi`(str) · `depth_check_vi`(str) · `analysis_vi`(str) · `tip_vi`(str) · `stretch_note`(str)

### `writing_guidance` (array)
Each: `task_id`(int) · `model_answer`(str) · `guidance_vi`(str) · `self_checklist`(str[])
**Key names are exact** — do not use `suggested_model_answer`, `step_by_step_guidance_vi`, or `self_check_vi`.

### `writing_revisions` (array, optional)
Each: `task_id`(int) · `original_prompt`(str) · `revised_prompt`(str) · `reason`(str)

### `review_bridge` (array, exactly 3 items)
Each: `id`(int) · `prompt`(str) · `correct_answer`(str) · `rationale_vi`(str)
**Key names are exact** — do not use `question_no`, `question`, `explanation_vi`, or `explanation`.

---

## `warm_up`
Array of strings (exactly 3 questions in English).
Instruction line must be `*Answer the following questions in English:*`.
