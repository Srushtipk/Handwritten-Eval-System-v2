import os
import json
import requests
import re
from sentence_transformers import SentenceTransformer, util

class HandwrittenEvaluator:
    def __init__(self):
        # Math Engine (Cosine Similarity)
        print("Initializing Semantic Embedding Model (Math Engine)...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # AI Engine (Ollama / LLaMA-3)
        self.api_url = "http://localhost:11434/api/generate"
        self.model_name = "my-evaluator"
        
    def _evaluate_exact(self, student_answer: str, ideal_answer: str):
        """
        Exact evaluation for queries/code/keywords.
        Checks if the key keywords in the ideal answer exist in the student's answer.
        """
        # A simple strict matching logic: calculate word overlap percentage
        ideal_words = set(re.findall(r'\w+', ideal_answer.lower()))
        student_words = set(re.findall(r'\w+', student_answer.lower()))
        
        if not ideal_words:
            return 1.0
            
        matches = ideal_words.intersection(student_words)
        # Apply a 30% leniency curve to exact keyword matching
        score = len(matches) / len(ideal_words)
        lenient_score = min(1.0, score * 1.3)
        return lenient_score
        
    def _evaluate_flexible(self, student_answer: str, ideal_answer: str):
        """
        Flexible evaluation using Cosine Similarity.
        """
        if not student_answer.strip():
            return 0.0
            
        emb_ideal = self.embedding_model.encode(ideal_answer, convert_to_tensor=True)
        emb_student = self.embedding_model.encode(student_answer, convert_to_tensor=True)
        
        cosine_scores = util.cos_sim(emb_ideal, emb_student)
        raw_score = cosine_scores[0][0].item()
        
        # Apply a 20% leniency curve to semantic matching
        lenient_score = min(1.0, raw_score * 1.2)
        return lenient_score
        
    def evaluate(self, question: str, ideal_rubric: str, max_marks: int, ocr_text: str, ans_type: str = 'flexible', min_length: str = None):
        """
        Dual-Engine Evaluation:
        1. Score generated via Mathematics (Sentence Transformers or Exact Match).
        2. Reasoning generated via AI (Ollama).
        """
        
        # === 1. MATH ENGINE (Score Calculation) ===
        if ans_type == 'exact':
            raw_score = self._evaluate_exact(ocr_text, ideal_rubric)
        else:
            raw_score = self._evaluate_flexible(ocr_text, ideal_rubric)
            
        # Apply length penalty if constraint is not met
        length_penalty = 0.0
        if min_length:
            # Simple heuristic: 1 page ~ 250 words
            pages_req = 1
            if '2' in min_length: pages_req = 2
            elif '3' in min_length: pages_req = 3
            
            words = len(ocr_text.split())
            if words < (pages_req * 150): # leniency on word count for handwriting
                length_penalty = 0.2 # 20% penalty
                
        final_percentage = max(0.0, raw_score - length_penalty)
        # Round off the marks to an integer as per university requirements
        final_marks = int(round(final_percentage * max_marks))
        
        # === 2. AI ENGINE (Reasoning Generation) ===
        instruction = "You are a teacher. In exactly 2 sentences, explain what key concepts the student missed or got right based on the rubric. DO NOT copy or repeat the student's text. Give only the feedback."
        
        input_text = (
            f"Question: {question}\n"
            f"Ideal Rubric: {ideal_rubric}\n"
            f"Student Answer (OCR): {ocr_text}\n"
            f"Score Awarded: {final_marks}/{max_marks}"
        )
        
        prompt = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n"
        
        reasoning = ""
        try:
            print("Requesting Reasoning from Local LLaMA-3...")
            response = requests.post(self.api_url, json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_ctx": 2048,
                    "stop": ["</s>", "### Instruction:"]
                }
            })
            
            if response.status_code == 200:
                response_text = response.json()['response'].strip()
                # If the fine-tuned model outputs JSON, try to extract reasoning, else use raw text
                try:
                    parsed = json.loads(response_text)
                    reasoning = parsed.get("reasoning", response_text)
                except:
                    reasoning = response_text
            else:
                reasoning = f"AI Engine Error: {response.text}"
        except Exception as e:
            reasoning = "AI Engine could not be reached. Score was calculated via Math Engine."

        return {
            "score": final_marks,
            "reasoning": reasoning,
            "match_percentage": round(raw_score * 100, 1),
            "penalty": round(length_penalty * 100, 1)
        }
