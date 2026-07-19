import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

ideal = "The process of photosynthesis involves the conversion of light energy into chemical energy by plants."
student_good = "Plants use sunlight to make food and chemical energy."
student_bad = "The mitochondria is the powerhouse of the cell."
student_short = "light into chemical energy"

emb_ideal = model.encode(ideal, convert_to_tensor=True)
print("Good:", util.cos_sim(emb_ideal, model.encode(student_good, convert_to_tensor=True))[0][0].item())
print("Bad:", util.cos_sim(emb_ideal, model.encode(student_bad, convert_to_tensor=True))[0][0].item())
print("Short:", util.cos_sim(emb_ideal, model.encode(student_short, convert_to_tensor=True))[0][0].item())
