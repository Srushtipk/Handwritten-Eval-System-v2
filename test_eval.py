import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.evaluation_engine import HandwrittenEvaluator

evaluator = HandwrittenEvaluator()
ideal = "The process of photosynthesis involves the conversion of light energy into chemical energy by plants."
student = "Plants use sunlight to make food and chemical energy."
print("=== Lenient ===")
print(evaluator.evaluate(ideal, student, 10, "flexible", grading_mode="lenient"))
print("=== Experienced ===")
print(evaluator.evaluate(ideal, student, 10, "flexible", grading_mode="experienced"))
