import os
import json
import requests
import re
from sentence_transformers import SentenceTransformer, util

class HandwrittenEvaluator:
    def __init__(self):
        print("Initializing True Hybrid Engine: Semantic Math + LLaMA Reasoning...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.api_url = "http://localhost:11434/api/generate"
        self.model_name = "my-evaluator"

    def _evaluate_exact(self, student_answer: str, ideal_answer: str):
        ideal_words = set(re.findall(r'\w+', ideal_answer.lower()))
        student_words = set(re.findall(r'\w+', student_answer.lower()))
        if not ideal_words: return 1.0
        matches = ideal_words.intersection(student_words)
        score = len(matches) / len(ideal_words)
        return min(1.0, score * 1.3)
        
    def _evaluate_flexible(self, student_answer: str, ideal_answer: str):
        if not student_answer.strip(): return 0.0
        emb_ideal = self.embedding_model.encode(ideal_answer, convert_to_tensor=True)
        emb_student = self.embedding_model.encode(student_answer, convert_to_tensor=True)
        cosine_scores = util.cos_sim(emb_ideal, emb_student)
        raw_score = cosine_scores[0][0].item()
        return min(1.0, raw_score * 1.2)

    def _run_hybrid_text_eval(self, ideal_rubric, ocr_text, text_max_marks, ans_type, grading_mode='experienced'):
        if text_max_marks <= 0: return 0.0
        
        if 'programming' in ans_type.lower() or 'exact' in ans_type.lower():
            raw_score = self._evaluate_exact(ocr_text, ideal_rubric)
        else:
            raw_score = self._evaluate_flexible(ocr_text, ideal_rubric)
            
        # Fix for Lenient vs Experienced mode
        if grading_mode == 'lenient':
            if raw_score >= 0.50:
                raw_score = 1.0 # Massive curve
            else:
                raw_score = min(1.0, raw_score * 1.5)
                
        return raw_score

    def _generate_llama_reasoning(self, ideal_rubric, student_answer, max_marks, awarded_marks, grading_mode):
        prompt = f"""
You are an AI assistant. The mathematical engine awarded this answer {awarded_marks}/{max_marks} marks.
Write exactly ONE short sentence (max 15 words) addressed to the student explaining why they got this score based on the rubric.
Be encouraging.

TEACHER RUBRIC: {ideal_rubric[:300]}
STUDENT ANSWER: {student_answer[:300]}

Return a JSON object: {{"reasoning": "your short sentence"}}
"""
        try:
            # STRICT 15 SECOND TIMEOUT to prevent freezing on local hardware!
            response = requests.post(self.api_url, json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }, timeout=15)
            
            res_json = response.json()
            llm_output = res_json.get('response', '{}')
            llm_output = llm_output.replace('```json', '').replace('```', '').strip()
            data = json.loads(llm_output)
            
            return str(data.get('reasoning', f"Your answer scored {awarded_marks}/{max_marks} based on semantic similarity to the rubric."))
            
        except requests.exceptions.Timeout:
            print("LLaMA API timed out! Falling back to standard response to prevent freezing.")
            return f"Your answer scored {awarded_marks}/{max_marks} based on semantic similarity to the rubric."
        except Exception as e:
            print(f"Error calling LLaMA API: {e}")
            return f"Your answer scored {awarded_marks}/{max_marks} based on semantic similarity to the rubric."

    def evaluate(self, ideal_rubric: str, ocr_text: str, max_marks: int, ans_type: str, components: dict = None, min_length: str = None, grading_mode: str = 'experienced', question: str = '') -> dict:
        if not ocr_text or len(ocr_text.strip()) < 5:
            return {
                'score': 0, 'match_percentage': 0, 'penalty': 0,
                'reasoning': "No valid answer provided.",
                'trace': [{"status": "error", "msg": "No valid answer provided."}]
            }
            
        # 1. Pure Math Grading
        raw_percentage = self._run_hybrid_text_eval(ideal_rubric, ocr_text, max_marks, ans_type, grading_mode)
        score = int(round(raw_percentage * max_marks))
        
        # 2. Length Penalty
        length_penalty = 0.0
        if min_length and str(min_length).lower() != 'none':
            student_words = set(re.findall(r'\b\w+\b', ocr_text.lower()))
            if len(student_words) < 20: 
                length_penalty = 0.2
                score = max(0, int(round((raw_percentage - length_penalty) * max_marks)))
        
        # 3. LLaMA Reasoning Generation (Sequential with Strict Timeout)
        reasoning = self._generate_llama_reasoning(ideal_rubric, ocr_text, max_marks, score, grading_mode)
        
        # Build Trace
        trace = []
        if score == max_marks:
            trace.append({"status": "success", "msg": reasoning})
        elif score > max_marks / 2:
            trace.append({"status": "warning", "msg": reasoning})
        else:
            trace.append({"status": "error", "msg": reasoning})
            
        return {
            "score": score,
            "match_percentage": raw_percentage,
            "penalty": length_penalty,
            "reasoning": reasoning,
            "trace": trace
        }
