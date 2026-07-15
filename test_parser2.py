import docx
from core.scheme_parser import SchemeParser

doc = docx.Document()
text = """Question 1a: Explain Continuous Deployment workflow with a neat diagram.
Max Marks: 7
Type: Flexible
Min Length: None
Diagram Marks: 2
If you attend this question must and should attend the very next question , the and 2a and 2b question is optional
Answer: Continuous deployment is an extension of Continuous Delivery (CD) that automates the entire CI/CD pipeline from the moment the developer commits code until it is deployed to production through all verification steps.

Question 1b : Illustrate the process of Packer installation by using manual and scripting types.
Max Marks: 8
Type: Flexible
Min Length: None
Answer: To install Packer manually, first download the appropriate package from the official Packer downloads page based on the operating system.
"""
doc.add_paragraph(text)
doc.save('test_scheme2.docx')

parser = SchemeParser()
questions = parser.parse_scheme('test_scheme2.docx')
for q in questions:
    print(f"ID: {q.get('id')}")
    print(f"Type: {q.get('type')}")
    print(f"Question: {q.get('question')}")
    print(f"Max Marks: {q.get('max_marks')}")
    print(f"Diagram Marks: {q.get('diagram_marks')}")
    print("---")
