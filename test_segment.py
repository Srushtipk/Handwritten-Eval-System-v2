from core.ocr_engine import segment_answers_with_gemini

raw_ocr = """--- Page 1 ---
1
CIE-I
Module-I

2a)
* Continous delivery comes after continous integration where the code after completion is staged into the staging area.
* Staging is the process of deploying in an environment where it is executed and tested before the release to production.
"""

# The IDs extracted from parser
q_ids = ['1a', '1b', '2', '2b']

print("Running segmentation...")
res = segment_answers_with_gemini(raw_ocr, q_ids)
print("Result:")
print(res)
