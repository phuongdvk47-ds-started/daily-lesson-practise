# PDF Layout Specification

## Page Setup
```css
@page { size: A4; margin: 14mm 13mm 16mm 13mm; }
```
A4 = 210mm × 297mm = 595.28pt × 841.89pt

## Footer
Every page: `[lession_id] | Page [current]/[total]`
Example: `LSN-012-B2-A7K9P2QX | Page 3/12`
- Font: 8pt, Times New Roman, color #666
- Center-aligned in bottom margin
- Must NOT overlap content
- Must be consistent across all pages

## Typography
- Body: Times New Roman, 10.5-11.5pt, line-height 1.45
- Headings: Bold, 11-16pt, color #1a365d / #2a4365
- IPA: Noto Sans or DejaVu Sans fallback
- Vietnamese: Full Unicode support required
- No browser-default fonts

## Tables
- Border collapse, 0.75pt borders
- Header row background #edf2f7
- Repeat headers on page break (if supported)
- No font smaller than 8pt
- No overflow beyond margins
- Alternative layout for wide tables (rotate or split)

## Images
- Preserve original images from source
- Never replace with AI-generated images
- Maintain aspect ratio
- No cropping that loses data
- Store originals + any resized versions
- Log any transformation

## Anti-Empty-Line Rules
- No `<br><br>` for spacing (use CSS margins)
- No empty paragraphs
- No empty table rows
- No empty sections
- No unnecessary page breaks
- No nearly-blank pages (< 10 chars)
- No excessive whitespace (> 40% of page area)

## Page Break Rules
- Headings: page-break-after: avoid
- Question blocks: page-break-inside: avoid
- Tips boxes: page-break-inside: avoid
- Grammar formulas: page-break-inside: avoid
- Tables: allow break between rows, not within rows
- Orphans: 3 minimum
- Widows: 3 minimum
