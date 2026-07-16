import os
import re
from sentence_transformers import SentenceTransformer, util

class HandwrittenEvaluator:
    def __init__(self):
        print("Initializing True Hybrid Engine: Semantic Math + Semantic Reasoning...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

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

    def _generate_semantic_reasoning(self, ideal_rubric: str, student_answer: str, max_marks: int, awarded_marks: int, grading_mode: str) -> str:
        """
        Splits the rubric into individual sentences and uses the already-loaded
        SentenceTransformer to find which rubric points are semantically absent
        from the student's answer. Quotes the actual missing rubric sentences directly.
        Zero additional downloads. Instant. Contextually aware.
        """
        # Split rubric into individual meaningful sentences/points
        rubric_sentences = [s.strip() for s in re.split(r'[.\n]|(?<=\d)\.', ideal_rubric) if len(s.strip()) > 15]
        
        if not rubric_sentences:
            percentage = (awarded_marks / max_marks * 100) if max_marks > 0 else 0
            return f"You scored {awarded_marks}/{max_marks} ({percentage:.0f}%)."
        
        # Encode rubric sentences and the full student answer
        rubric_embeddings = self.embedding_model.encode(rubric_sentences, convert_to_tensor=True)
        student_embedding = self.embedding_model.encode(student_answer, convert_to_tensor=True)
        
        # Compute cosine similarity of student answer against each rubric sentence
        similarities = util.cos_sim(student_embedding, rubric_embeddings)[0]
        
        # Threshold: rubric points with similarity < 0.35 are considered "missing"
        threshold = 0.35
        missing_points = [
            rubric_sentences[i]
            for i in range(len(rubric_sentences))
            if similarities[i].item() < threshold
        ]
        
        # Build the feedback message
        percentage = (awarded_marks / max_marks * 100) if max_marks > 0 else 0
        
        if awarded_marks == max_marks:
            prefix = f"Excellent work! You scored full marks ({awarded_marks}/{max_marks})."
            return f"{prefix} All key points from the rubric were addressed."
        elif percentage >= 75:
            prefix = f"Good attempt. You scored {awarded_marks} out of {max_marks} marks."
        elif percentage >= 50:
            prefix = f"Satisfactory. You scored {awarded_marks} out of {max_marks} marks."
        elif percentage >= 25:
            prefix = f"You scored {awarded_marks} out of {max_marks} marks."
        else:
            prefix = f"You scored {awarded_marks} out of {max_marks} marks. Significant improvement needed."
        
        if not missing_points:
            return f"{prefix} The answer covered most rubric points but lacked depth."
        
        # Format missing points as a clean bulleted list
        missing_str = "; ".join(f'"{p}"' for p in missing_points[:4])
        return f"{prefix} The following rubric points were not adequately addressed: {missing_str}."

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
        
        # 3. Semantic Sentence-Gap Reasoning (uses existing model, instant, specific)
        reasoning = self._generate_semantic_reasoning(ideal_rubric, ocr_text, max_marks, score, grading_mode)
        
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
