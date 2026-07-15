from core.scheme_parser import SchemeParser
from core.ocr_engine import segment_answers_with_gemini

# Mocking a parser
parser = SchemeParser()
questions = parser.parse_scheme('test_scheme2.docx')
print(type(questions))
print(type(questions[0]))

try:
    res = segment_answers_with_gemini("dummy text", questions)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
