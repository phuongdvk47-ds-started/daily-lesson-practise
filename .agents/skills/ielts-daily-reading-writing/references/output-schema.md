# Output JSON Schema Specification

This document defines the JSON structure of `lesson_source.json`, which is the Single Source of Truth for daily IELTS packs.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "IELTSDailyLessonSource",
  "type": "OBJECT",
  "properties": {
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
        "writing_task_count": { "type": "INTEGER" }
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
              "stretch": { "type": "BOOLEAN" }
            },
            "required": ["id", "type", "question", "correct_answer", "evidence_paragraph", "evidence_quote", "rationale_vi", "stretch"]
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
              "source": { "type": "STRING", "enum": ["reading", "topic-extension"] }
            },
            "required": ["id", "term", "ipa", "part_of_speech", "definition_en", "meaning_vi", "example", "source"]
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
              "stretch": { "type": "BOOLEAN" }
            },
            "required": ["id", "type", "question", "correct_answer", "explanation_vi", "stretch"]
          }
        }
      },
      "required": ["targets", "guide", "common_mistakes", "questions"]
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
              }
            },
            "required": ["id", "task_type", "prompt", "target_length", "focus_skill", "useful_language", "success_criteria", "visual_data"]
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
    }
  },
  "required": ["lesson_meta", "source", "reading", "vocabulary", "grammar", "writing", "answers"]
}
```
