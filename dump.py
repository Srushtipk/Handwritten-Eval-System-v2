import docx
import json

doc = docx.Document('data/uploads/Question.docx')
lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
with open('test_dump.json', 'w', encoding='utf-8') as f:
    json.dump(lines, f, indent=2)
