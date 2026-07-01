# Output JSON Schema Specification

This document defines the JSON structure of `lesson_source.json`, which is the Single Source of Truth for daily IELTS packs.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "IELTSDailyLessonSource",
  "type": "OBJECT",
  "properties": {
    "execution": {
      "type": "OBJECT",
      "properties": {
        "mode": { "type": "STRING", "enum": ["auto", "review"] },
        "pipeline_status": { "type": "STRING", "enum": ["draft", "reviewing", "qc_failed", "qc_passed", "exported"] },
        "current_stage": { "type": "STRING" },
        "revision_attempts": {
          "type": "OBJECT",
          "properties": {
            "source": { "type": "INTEGER" },
            "reading": { "type": "INTEGER" },
            "vocabulary": { "type": "INTEGER" },
            "grammar": { "type": "INTEGER" },
            "writing": { "type": "INTEGER" },
            "answers": { "type": "INTEGER" },
            "pdf_layout": { "type": "INTEGER" }
          },
          "required": ["source", "reading", "vocabulary", "grammar", "writing", "answers", "pdf_layout"]
        }
      },
      "required": ["mode", "pipeline_status", "current_stage", "revision_attempts"]
    },
    "human_review": {
      "type": "OBJECT",
      "properties": {
        "mode": { "type": "STRING", "enum": ["auto", "review"] },
        "checkpoints": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "checkpoint": { "type": "STRING" },
              "status": { "type": "STRING", "enum": ["approved", "rejected", "revised", "skipped"] },
              "user_instruction": { "type": "STRING" },
              "decision_time": { "type": "STRING" },
              "affected_sections": {
                "type": "ARRAY",
                "items": { "type": "STRING" }
              }
            },
            "required": ["checkpoint", "status", "user_instruction", "decision_time", "affected_sections"]
          }
        }
      },
      "required": ["mode", "checkpoints"]
    },
    "agent_review": {
      "type": "OBJECT",
      "properties": {
        "reviews": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "reviewer_agent": { "type": "STRING" },
              "reviewed_section": { "type": "STRING" },
              "review_status": { "type": "STRING", "enum": ["pass", "challenge"] },
              "strengths": {
                "type": "ARRAY",
                "items": { "type": "STRING" }
              },
              "challenges": {
                "type": "ARRAY",
                "items": { "type": "STRING" }
              }
            },
            "required": ["reviewer_agent", "reviewed_section", "review_status", "strengths", "challenges"]
          }
        },
        "challenges": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "id": { "type": "STRING" },
              "from_agent": { "type": "STRING" },
              "to_agent": { "type": "STRING" },
              "challenge_type": {
                "type": "STRING",
                "enum": [
                  "source_quality",
                  "level_mismatch",
                  "ambiguity",
                  "multiple_answers",
                  "multiple_valid_answers",
                  "missing_evidence",
                  "insufficient_context",
                  "weak_distractor",
                  "keyword_scanning",
                  "vocabulary_imbalance",
                  "missing_vocab_type",
                  "grammar_target_mismatch",
                  "logic_error",
                  "incomplete_punctuation",
                  "incomplete_inserted_option",
                  "missing_error_in_error_correction",
                  "answer_identical_to_prompt",
                  "explanation_mismatch",
                  "writing_visual_missing",
                  "answer_explanation_weak",
                  "pdf_layout_risk",
                  "schema_error",
                  "human_preference_required",
                  "numbering_error",
                  "meaning_changed",
                  "topic_alignment",
                  "time_workload_mismatch"
                ]
              },
              "severity": { "type": "STRING", "enum": ["low", "medium", "high", "critical"] },
              "location": { "type": "STRING" },
              "problem": { "type": "STRING" },
              "required_fix": { "type": "STRING" },
              "status": { "type": "STRING", "enum": ["open", "resolved", "accepted_by_user", "rejected"] },
              "revision_attempt": { "type": "INTEGER" }
            },
            "required": ["id", "from_agent", "to_agent", "challenge_type", "severity", "location", "problem", "required_fix", "status", "revision_attempt"]
          }
        }
      },
      "required": ["reviews", "challenges"]
    },
    "lesson_meta": {
      "type": "OBJECT",
      "properties": {
        "lesson_id": { "type": "STRING", "description": "Unique format LSN-[Day]-[Level]-[Random8]" },
        "day": { "type": "STRING", "description": "YYYYMMDD format" },
        "level": { "type": "STRING", "enum": ["A1", "A2", "B1", "B2", "C1", "C2"] },
        "theme": { "type": "STRING" },
        "topic": { "type": "STRING" },
        "specific_topic": { "type": "STRING" },
        "created_at": { "type": "STRING" },
        "reading_question_count": { "type": "INTEGER" },
        "vocabulary_count": { "type": "INTEGER" },
        "grammar_question_count": { "type": "INTEGER" },
        "writing_task_count": { "type": "INTEGER" },
        "printed_time_allowed_minutes": { "type": "INTEGER" },
        "estimated_completion_time_minutes": { "type": "INTEGER" },
        "time_workload_status": { "type": "STRING", "enum": ["ok", "warning", "mismatch"] }
      },
      "required": ["lesson_id", "day", "level", "theme", "topic", "specific_topic", "created_at", "reading_question_count", "vocabulary_count", "grammar_question_count", "writing_task_count"]
    },
    "source": {
      "type": "OBJECT",
      "properties": {
        "status": { "type": "STRING", "enum": ["verified", "failed"] },
        "source_title": { "type": "STRING" },
        "publisher": { "type": "STRING" },
        "author": { "type": "STRING" },
        "published_date": { "type": "STRING" },
        "verified_url": { "type": "STRING" },
        "access_date": { "type": "STRING" },
        "url_status": { "type": "STRING" },
        "credibility_note": { "type": "STRING" },
        "topic_relevance_note": { "type": "STRING" },
        "usable_excerpt": { "type": "STRING" },
        "copyright_note": { "type": "STRING" },
        "failure_reason": { "type": "STRING" }
      },
      "required": ["status", "source_title", "publisher", "verified_url"]
    },
    "reading": {
      "type": "OBJECT",
      "properties": {
        "passage": {
          "type": "OBJECT",
          "properties": {
            "title": { "type": "STRING" },
            "paragraphs": {
              "type": "ARRAY",
              "items": {
                "type": "OBJECT",
                "properties": {
                  "id": { "type": "INTEGER" },
                  "text": { "type": "STRING" }
                },
                "required": ["id", "text"]
              }
            }
          },
          "required": ["title", "paragraphs"]
        },
        "questions": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "id": { "type": "INTEGER" },
              "type": { "type": "STRING" },
              "question": { "type": "STRING" },
              "options": {
                "type": "ARRAY",
                "items": { "type": "STRING" }
              },
              "correct_answer": { "type": "STRING" },
              "evidence_paragraph": { "type": "INTEGER" },
              "evidence_quote": { "type": "STRING" },
              "rationale_vi": { "type": "STRING" },
              "reasoning_skill": { "type": "STRING", "enum": ["literal", "paraphrase", "inference", "comparison", "cause_effect", "contrast", "classification", "writer_purpose"] },
              "source_scope": { "type": "STRING", "enum": ["printed_passage_only"] },
              "stretch": { "type": "BOOLEAN" }
            },
            "required": ["id", "type", "question", "correct_answer", "evidence_paragraph", "evidence_quote", "rationale_vi", "reasoning_skill", "source_scope", "stretch"]
          }
        }
      },
      "required": ["passage", "questions"]
    },
    "vocabulary": {
      "type": "OBJECT",
      "properties": {
        "items": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "id": { "type": "INTEGER" },
              "term": { "type": "STRING" },
              "ipa": { "type": "STRING" },
              "part_of_speech": { "type": "STRING" },
              "definition_en": { "type": "STRING" },
              "meaning_vi": { "type": "STRING" },
              "example": { "type": "STRING" },
              "vocab_type": { "type": "STRING", "enum": ["single_word", "phrase", "idiom", "fixed_expression", "collocation", "topic_vocabulary", "academic_vocabulary"] },
              "source": { "type": "STRING", "enum": ["reading", "topic-extension"] }
            },
            "required": ["id", "term", "ipa", "part_of_speech", "definition_en", "meaning_vi", "example", "vocab_type", "source"]
          }
        },
        "recycled_items": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "term": { "type": "STRING" },
              "ipa": { "type": "STRING" },
              "part_of_speech": { "type": "STRING" },
              "meaning_vi": { "type": "STRING" },
              "source_day": { "type": "STRING" }
            },
            "required": ["term", "ipa", "part_of_speech", "meaning_vi", "source_day"]
          }
        },
        "quizlet": {
          "type": "OBJECT",
          "properties": {
            "section_1_simple": {
              "type": "ARRAY",
              "items": { "type": "STRING" }
            },
            "section_2_detailed": {
              "type": "ARRAY",
              "items": { "type": "STRING" }
            }
          },
          "required": ["section_1_simple", "section_2_detailed"]
        },
        "vocab_checker_items": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "term": { "type": "STRING" },
              "ipa": { "type": "STRING" },
              "part_of_speech": { "type": "STRING" },
              "definition_en": { "type": "STRING" },
              "meaning_vi": { "type": "STRING" }
            },
            "required": ["term", "ipa", "part_of_speech", "definition_en", "meaning_vi"]
          }
        }
      },
      "required": ["items", "recycled_items", "quizlet", "vocab_checker_items"]
    },
    "grammar": {
      "type": "OBJECT",
      "properties": {
        "targets": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "name": { "type": "STRING" },
              "level": { "type": "STRING" },
              "reason": { "type": "STRING" }
            },
            "required": ["name", "level", "reason"]
          }
        },
        "guide": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "heading": { "type": "STRING" },
              "content": { "type": "STRING" }
            },
            "required": ["heading", "content"]
          }
        },
        "common_mistakes": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "trap": { "type": "STRING" },
              "wrong_example": { "type": "STRING" },
              "correct_version": { "type": "STRING" },
              "why_it_matters": { "type": "STRING" }
            },
            "required": ["trap", "wrong_example", "correct_version", "why_it_matters"]
          }
        },
        "sections": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "section_title": { "type": "STRING" },
              "internal_question_start": { "type": "INTEGER" },
              "internal_question_end": { "type": "INTEGER" },
              "display_question_start": { "type": ["integer", "null"] },
              "display_question_end": { "type": ["integer", "null"] },
              "compiler_computed_range": { "type": "BOOLEAN" }
            },
            "required": ["section_title", "internal_question_start", "internal_question_end", "compiler_computed_range"]
          }
        },
        "questions": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "id": { "type": "INTEGER" },
              "type": { "type": "STRING" },
              "question": { "type": "STRING" },
              "options": {
                "type": "ARRAY",
                "items": { "type": "STRING" }
              },
              "correct_answer": { "type": "STRING" },
              "explanation_vi": { "type": "STRING" },
              "stretch": { "type": "BOOLEAN" },
              "logic_validation": {
                "type": "OBJECT",
                "properties": {
                  "has_exactly_one_valid_answer": { "type": "BOOLEAN" },
                  "context_is_sufficient": { "type": "BOOLEAN" },
                  "final_sentence_after_insertion": { "type": "STRING" },
                  "why_correct_is_unique": { "type": "STRING" },
                  "why_other_options_are_wrong": {
                    "type": "ARRAY",
                    "items": {
                      "type": "OBJECT",
                      "properties": {
                        "option": { "type": "STRING" },
                        "reason": { "type": "STRING" }
                      },
                      "required": ["option", "reason"]
                    }
                  },
                  "punctuation_complete": { "type": "BOOLEAN" },
                  "meaning_preserved": { "type": "BOOLEAN" },
                  "target_structure_clear": { "type": "BOOLEAN" },
                  "answer_family_is_bounded": { "type": "BOOLEAN" },
                  "example_expected_answer": { "type": "STRING" },
                  "alternative_answers_allowed": {
                    "type": "ARRAY",
                    "items": { "type": "STRING" }
                  }
                },
                "required": ["has_exactly_one_valid_answer", "context_is_sufficient", "punctuation_complete", "meaning_preserved"]
              },
              "error_correction_validation": {
                "type": "OBJECT",
                "properties": {
                  "original_sentence": { "type": "STRING" },
                  "corrected_sentence": { "type": "STRING" },
                  "target_error_text": { "type": "STRING" },
                  "target_error_type": { "type": "STRING" },
                  "correction_text": { "type": "STRING" },
                  "original_contains_error": { "type": "BOOLEAN" },
                  "corrected_differs_from_original": { "type": "BOOLEAN" },
                  "exactly_one_target_error": { "type": "BOOLEAN" },
                  "explanation_matches_error": { "type": "BOOLEAN" }
                },
                "required": ["original_sentence", "corrected_sentence", "target_error_text", "correction_text", "original_contains_error", "corrected_differs_from_original", "explanation_matches_error"]
              }
            },
            "required": ["id", "type", "question", "correct_answer", "explanation_vi", "stretch", "logic_validation"]
          }
        }
      },
      "required": ["targets", "guide", "common_mistakes", "sections", "questions"]
    },
    "writing": {
      "type": "OBJECT",
      "properties": {
        "tasks": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "id": { "type": "INTEGER" },
              "task_type": { "type": "STRING" },
              "prompt": { "type": "STRING" },
              "target_length": { "type": "STRING" },
              "focus_skill": { "type": "STRING" },
              "useful_language": {
                "type": "ARRAY",
                "items": { "type": "STRING" }
              },
              "success_criteria": {
                "type": "ARRAY",
                "items": { "type": "STRING" }
              },
              "visual_data": {
                "type": "OBJECT",
                "properties": {
                  "type": { "type": "STRING", "enum": ["none", "markdown_table", "svg"] },
                  "content": { "type": "STRING" }
                },
                "required": ["type", "content"]
              },
              "topic_alignment": { "type": "BOOLEAN" }
            },
            "required": ["id", "task_type", "prompt", "target_length", "focus_skill", "useful_language", "success_criteria", "visual_data", "topic_alignment"]
          }
        }
      },
      "required": ["tasks"]
    },
    "answers": {
      "type": "OBJECT",
      "properties": {
        "reading_answers": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "question_id": { "type": "INTEGER" },
              "correct_answer": { "type": "STRING" },
              "evidence_quote": { "type": "STRING" },
              "evidence_paragraph": { "type": "INTEGER" },
              "explanation_vi": { "type": "STRING" },
              "why_others_wrong_vi": { "type": "STRING" },
              "tip_vi": { "type": "STRING" },
              "stretch_note": { "type": "STRING" }
            },
            "required": ["question_id", "correct_answer", "evidence_quote", "evidence_paragraph", "explanation_vi", "why_others_wrong_vi", "tip_vi"]
          }
        },
        "grammar_answers": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "question_id": { "type": "INTEGER" },
              "correct_answer": { "type": "STRING" },
              "analysis_vi": { "type": "STRING" },
              "tip_vi": { "type": "STRING" },
              "stretch_note": { "type": "STRING" }
            },
            "required": ["question_id", "correct_answer", "analysis_vi", "tip_vi"]
          }
        },
        "writing_guidance": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "task_id": { "type": "INTEGER" },
              "model_answer": { "type": "STRING" },
              "guidance_vi": { "type": "STRING" },
              "self_checklist": {
                "type": "ARRAY",
                "items": { "type": "STRING" }
              }
            },
            "required": ["task_id", "model_answer", "guidance_vi", "self_checklist"]
          }
        },
        "writing_revisions": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "task_id": { "type": "INTEGER" },
              "original_prompt": { "type": "STRING" },
              "revised_prompt": { "type": "STRING" },
              "reason": { "type": "STRING" }
            },
            "required": ["task_id", "original_prompt", "revised_prompt", "reason"]
          }
        },
        "review_bridge": {
          "type": "ARRAY",
          "items": {
            "type": "OBJECT",
            "properties": {
              "id": { "type": "INTEGER" },
              "prompt": { "type": "STRING" },
              "correct_answer": { "type": "STRING" },
              "rationale_vi": { "type": "STRING" }
            },
            "required": ["id", "prompt", "correct_answer", "rationale_vi"]
          }
        }
      },
      "required": ["reading_answers", "grammar_answers", "writing_guidance", "review_bridge"]
    },
    "warm_up": {
      "type": "ARRAY",
      "items": {
        "type": "STRING"
      }
    }
  },
  "required": [
    "execution",
    "human_review",
    "agent_review",
    "lesson_meta",
    "source",
    "reading",
    "vocabulary",
    "grammar",
    "writing",
    "answers",
    "warm_up"
  ]
}
```
