import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.evaluation_engine import HandwrittenEvaluator

evaluator = HandwrittenEvaluator()

ideal = "Photosynthesis requires sunlight, carbon dioxide, and water to produce glucose and oxygen."
student = "It needs sun and water to make food."

print("=== Lenient ===")
print(evaluator.evaluate(ideal, student, 10, "flexible", grading_mode="lenient"))
print("=== Experienced ===")
print(evaluator.evaluate(ideal, student, 10, "flexible", grading_mode="experienced"))
