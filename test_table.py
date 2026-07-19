import docx, re, json
doc = docx.Document('IA2-Scheme.docx')
questions = []
for table in doc.tables:
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
        if len(cells) >= 3:
            q_col = cells[0].lower().replace('q', '').strip()
            if re.match(r'^\d+$', q_col):
                q_id = q_col
                if re.match(r'^[a-z]\)?$', cells[1].lower()):
                    q_id += cells[1].replace(')', '')
                    text_cell = cells[2]
                    marks_cell = cells[3] if len(cells) > 3 else "10"
                else:
                    text_cell = cells[1]
                    marks_cell = cells[2]
                marks = 10
                m = re.search(r'(\d+)', marks_cell)
                if m: marks = int(m.group(1))
                lines = [line.strip() for line in text_cell.split('\n') if line.strip()]
                q_title = lines[0] if lines else "Question"
                questions.append({
                    'id': q_id, 'question': q_title, 'max_marks': marks, 'type': 'flexible', 'answer': text_cell
                })
print(json.dumps(questions, indent=2))
