# Blueprint Rules for Deep Reading and Deep Grammar

Before generating the actual questions for the Reading and Grammar sections, the agents **MUST** generate a blueprint JSON block defining the strategy, type, depth, evidence/context plan, and target skill for each question.
This prevents the generation of repetitive, mechanical, or surface-level items.

## 1. Deep Reading Ratio by Level

The Reading Agent must distribute questions according to these maximum/minimum ratios:

| Level | Literal | Inference / Reasoning | Function / Structure / Purpose | Vocab / Reference |
| ----- | ------: | --------------------: | -------------------: | ---------------: |
| A1    |   <=70% |                 >=10% |                >=10% |            >=10% |
| A1+   |   <=60% |                 >=15% |                >=10% |            >=15% |
| A2    |   <=50% |                 >=20% |                >=15% |            >=15% |
| A2+   |   <=45% |                 >=25% |                >=15% |            >=15% |
| B1    |   <=40% |                 >=30% |                >=15% |            >=15% |
| B1+   |   <=35% |                 >=35% |                >=15% |            >=15% |
| B2    |   <=30% |                 >=40% |                >=15% |            >=15% |
| B2+   |   <=25% |                 >=45% |                >=15% |            >=15% |
| C1    |   <=20% |                 >=45% |                >=20% |            >=15% |
| C1+   |   <=15% |                 >=50% |                >=20% |            >=15% |
| C2    |   <=10% |                 >=50% |                >=25% |            >=10% |

## 2. Deep Grammar Ratio by Level

The Grammar Agent must distribute questions according to these maximum/minimum ratios:

| Level | Mechanical Form | Meaning Contrast | Context/Discourse | Transformation/Error Correction |
| ----- | --------------: | ---------------: | ----------------: | ------------------------------: |
| A1    |          <=60% |            >=20% |             >=10% |                           >=10% |
| A1+   |          <=55% |            >=20% |             >=15% |                           >=10% |
| A2    |          <=45% |            >=25% |             >=15% |                           >=15% |
| A2+   |          <=40% |            >=25% |             >=20% |                           >=15% |
| B1    |          <=30% |            >=30% |             >=20% |                           >=20% |
| B1+   |          <=25% |            >=30% |             >=25% |                           >=20% |
| B2    |          <=20% |            >=30% |             >=30% |                           >=20% |
| B2+   |          <=15% |            >=30% |             >=35% |                           >=20% |
| C1    |          <=10% |            >=30% |             >=35% |                           >=25% |
| C1+   |          <=10% |            >=30% |             >=40% |                           >=25% |
| C2    |           <=5% |            >=30% |             >=40% |                           >=30% |

## 3. Mandatory Blueprint Output Format

Both agents must output a `blueprint` section in their JSON payload BEFORE outputting the actual questions.

### Reading Blueprint Format
```json
{
  "reading_blueprint": [
    {
      "question_no": 1,
      "type": "literal",
      "depth": "low",
      "target_skill": "identify explicitly stated information",
      "evidence_strategy": "single sentence",
      "distractor_strategy": "paraphrased but incorrect detail"
    },
    {
      "question_no": 2,
      "type": "inference",
      "depth": "medium",
      "target_skill": "infer reason from contrast between two sentences",
      "evidence_strategy": "multiple sentences",
      "distractor_strategy": "true detail but wrong reason"
    }
  ]
}
```

### Grammar Blueprint Format
```json
{
  "grammar_blueprint": [
    {
      "question_no": 1,
      "grammar_target": "present perfect vs past simple",
      "question_type": "contextual choice",
      "depth": "medium",
      "tested_dimension": "meaning/use",
      "trap": "past time phrase distractor"
    }
  ]
}
```

## 4. Blueprint Generation Rules

1. **Count Match**: The blueprint must contain exactly `reading_question_count` items for Reading, and `grammar_question_count` items for Grammar.
2. **Distribution Match**: The types generated in the blueprint must align with the level-specific maximum/minimum ratios. If the count is small, use minimum coverage rules rather than forcing impossible exact percentages.
3. **Diversity Rule**: The blueprint must not cluster identical target skills. E.g., Do not have 5 literal questions back to back. Do not have 5 tense drills back to back.
4. **Execution Alignment**: The actual questions generated subsequently MUST follow the blueprint exactly. The PDF Checker will verify this alignment.
5. **Required Fields**: Reading blueprint items require `question_no`, `type`, `depth`, `target_skill`, `evidence_strategy`, and `distractor_strategy`. Grammar blueprint items require `question_no`, `grammar_target`, `question_type`, `depth`, `tested_dimension`, and `trap`.
