# Local Open-Source Stack

## Approved Libraries

### PDF & Document Processing
| Library | Version | License | Purpose |
|---------|---------|---------|---------|
| PyMuPDF (fitz) | ≥1.24 | AGPL-3.0 | Text/image extraction, PDF inspection |
| pdfplumber | ≥0.11 | MIT | Table extraction, text extraction fallback |
| pypdf | ≥4.0 | BSD-3 | PDF metadata, page manipulation |

### OCR & Image
| Library | Version | License | Purpose |
|---------|---------|---------|---------|
| Tesseract OCR | ≥5.0 | Apache-2.0 | OCR fallback |
| PaddleOCR | ≥2.7 | Apache-2.0 | Primary OCR engine |
| Pillow | ≥10.0 | PIL | Image processing |

### HTML/CSS/PDF Rendering
| Library | Version | License | Purpose |
|---------|---------|---------|---------|
| Jinja2 | ≥3.1 | BSD-3 | HTML template rendering |
| Playwright | ≥1.40 | Apache-2.0 | HTML→PDF via Chromium |

### Validation
| Library | Version | License | Purpose |
|---------|---------|---------|---------|
| jsonschema | ≥4.0 | MIT | JSON Schema validation |

### NLP (optional, for local model stages)
| Library | Version | License | Purpose |
|---------|---------|---------|---------|
| spaCy | ≥3.7 | MIT | POS tagging, NER, sentence segmentation |
| NLTK | ≥3.8 | Apache-2.0 | Tokenization fallback |

## Selection Criteria
Each library must satisfy:
1. Open-source license compatible with project
2. Runs locally without external API calls
3. Stable, well-maintained, documented
4. Compatible with Python 3.10+ on Windows
5. Reasonable install size and dependencies
