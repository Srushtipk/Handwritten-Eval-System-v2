import os
import re
from sentence_transformers import SentenceTransformer, util

class HandwrittenEvaluator:
    def __init__(self):
        print("Initializing True Hybrid Engine: Semantic Math + Python Reasoning...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Stop words to ignore in keyword analysis
        self._stop_words = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
            'used', 'to', 'of', 'in', 'on', 'at', 'by', 'for', 'with', 'about',
            'as', 'it', 'its', 'this', 'that', 'these', 'those', 'and', 'or',
            'but', 'not', 'from', 'into', 'through', 'during', 'before', 'after',
            'also', 'which', 'who', 'what', 'how', 'when', 'where', 'if', 'so',
            'then', 'than', 'each', 'any', 'all', 'both', 'few', 'more', 'most',
            'other', 'such', 'no', 'nor', 'only', 'own', 'same', 'so', 'very',
            'just', 'because', 'while', 'although', 'however', 'therefore', 'thus'
        }

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

    def _extract_key_concepts(self, text: str) -> list:
        """Extract meaningful multi-word and single-word key concepts from rubric text."""
        text_lower = text.lower()
        
        # Extract multi-word technical phrases (2-3 words not in stopwords)
        phrases = []
        words = re.findall(r'[a-zA-Z][a-zA-Z0-9_-]*', text_lower)
        # Build bigrams and trigrams
        for i in range(len(words)):
            w = words[i]
            if w not in self._stop_words and len(w) > 3:
                phrases.append(w)
            if i < len(words) - 1:
                w2 = words[i+1]
                if w not in self._stop_words and w2 not in self._stop_words and len(w) > 2 and len(w2) > 2:
                    phrases.append(f"{w} {w2}")
        
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for p in phrases:
            if p not in seen:
                seen.add(p)
                unique.append(p)
        return unique

    def _generate_python_reasoning(self, ideal_rubric: str, student_answer: str, max_marks: int, awarded_marks: int, grading_mode: str) -> str:
        """Generate accurate, specific feedback purely in Python by comparing rubric vs student answer."""
        
        rubric_lower = ideal_rubric.lower()
        student_lower = student_answer.lower()
        
        # --- Step 1: Find key concepts in rubric that are MISSING from student answer ---
        rubric_concepts = self._extract_key_concepts(ideal_rubric)
        
        missing_concepts = []
        covered_concepts = []
        
        for concept in rubric_concepts:
            if concept in student_lower:
                covered_concepts.append(concept)
            else:
                missing_concepts.append(concept)
        
        # --- Step 2: Deduplicate missing concepts (remove if a longer phrase already captures it) ---
        # e.g., if 'git push' is missing, don't also report 'push' separately
        final_missing = []
        for c in missing_concepts:
            # Only keep it if no longer phrase containing this word was already added
            if not any(c in longer for longer in final_missing if longer != c):
                final_missing.append(c)
        
        # Limit to top 4 most impactful missing concepts
        top_missing = final_missing[:4]
        top_covered = covered_concepts[:3]
        
        # --- Step 3: Build the feedback message ---
        percentage = (awarded_marks / max_marks * 100) if max_marks > 0 else 0
        
        # Opening line based on score
        if awarded_marks == max_marks:
            opening = f"Excellent work! You scored full marks ({awarded_marks}/{max_marks})."
        elif percentage >= 75:
            opening = f"Good attempt. You scored {awarded_marks} out of {max_marks} marks."
        elif percentage >= 50:
            opening = f"Satisfactory. You scored {awarded_marks} out of {max_marks} marks, but there is room for improvement."
        elif percentage >= 25:
            opening = f"You scored {awarded_marks} out of {max_marks} marks. Several key concepts need attention."
        else:
            opening = f"You scored {awarded_marks} out of {max_marks} marks. The answer requires significant improvement."
        
        # What was covered — REMOVED: only show what is wrong
        covered_line = ""
        
        # What was missing
        missing_line = ""
        if top_missing:
            missing_line = f" However, the following key points from the rubric were missing or insufficiently explained: {', '.join(top_missing)}."
        elif awarded_marks == max_marks:
            missing_line = " All key points from the rubric were addressed."
        
        # Mode-specific advice
        if grading_mode == 'strict' and top_missing:
            advice = " In strict mode, all rubric points must be explicitly addressed."
        elif grading_mode == 'lenient' and top_missing:
            advice = " A more detailed explanation of the missing points would improve your score further."
        else:
            advice = ""
        
        return f"{opening}{missing_line}{advice}"

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
        
        # 3. Pure Python Reasoning (zero API calls, instant, accurate)
        reasoning = self._generate_python_reasoning(ideal_rubric, ocr_text, max_marks, score, grading_mode)
        
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
