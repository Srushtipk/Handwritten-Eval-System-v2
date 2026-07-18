import os
import re
from sentence_transformers import SentenceTransformer, util

class HandwrittenEvaluator:
    def __init__(self):
        print("Initializing True Hybrid Engine: Semantic Math + Semantic Reasoning...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        # Caches to prevent re-computing embeddings for the same rubric text
        self.ideal_embedding_cache = {}
        self.rubric_sentences_cache = {}

    def _evaluate_exact(self, student_answer: str, ideal_answer: str, grading_mode: str = 'experienced'):
        ideal_words = set(re.findall(r'\w+', ideal_answer.lower()))
        student_words = set(re.findall(r'\w+', student_answer.lower()))
        if not ideal_words: return 1.0
        matches = ideal_words.intersection(student_words)
        score = len(matches) / len(ideal_words)
        
        if grading_mode == 'lenient':
            threshold_min = 0.10
            threshold_max = 0.50
        else:
            threshold_min = 0.25
            threshold_max = 0.70
            
        if score < threshold_min:
            return 0.0
        return min(1.0, (score - threshold_min) / (threshold_max - threshold_min))
        
    def _evaluate_flexible(self, student_answer: str, ideal_answer: str, grading_mode: str = 'experienced'):
        if not student_answer.strip(): return 0.0
        
        # Use cache for ideal_answer embedding
        if ideal_answer not in self.ideal_embedding_cache:
            self.ideal_embedding_cache[ideal_answer] = self.embedding_model.encode(ideal_answer, convert_to_tensor=True)
        emb_ideal = self.ideal_embedding_cache[ideal_answer]
        
        emb_student = self.embedding_model.encode(student_answer, convert_to_tensor=True)
        cosine_scores = util.cos_sim(emb_ideal, emb_student)
        raw_score = cosine_scores[0][0].item()
        
        # Median Strictness Normalization Mapping:
        # Based on all-MiniLM-L6-v2 empirical testing: 0.70+ is an excellent match, ~0.30 is poor.
        if grading_mode == 'lenient':
            threshold_min = 0.20
            threshold_max = 0.60
        else:
            threshold_min = 0.40
            threshold_max = 0.75
            
        if raw_score < threshold_min:
            normalized_score = 0.0
        elif raw_score >= threshold_max:
            normalized_score = 1.0
        else:
            normalized_score = (raw_score - threshold_min) / (threshold_max - threshold_min)
            
        # Length-based Completeness Factor:
        # If a student answer is extremely short, it cannot be a complete answer
        # even if it has high semantic similarity to a key sentence.
        student_words = re.findall(r'\b\w+\b', student_answer.lower())
        ideal_words = re.findall(r'\b\w+\b', ideal_answer.lower())
        
        if len(ideal_words) > 10 and grading_mode != 'lenient':
            # We expect the student's answer to have at least 65% of the ideal answer's word count.
            target_length = max(8, int(len(ideal_words) * 0.65))
            length_ratio = len(student_words) / target_length
            completeness_factor = min(1.0, length_ratio)
            # Smooth the factor so it doesn't penalize slightly concise answers too heavily (0.2 baseline)
            completeness_factor = 0.2 + 0.8 * completeness_factor
            normalized_score = normalized_score * completeness_factor
            
        return normalized_score

    def _run_hybrid_text_eval(self, ideal_rubric, ocr_text, text_max_marks, ans_type, grading_mode='experienced'):
        if text_max_marks <= 0: return 0.0
        
        if 'programming' in ans_type.lower() or 'exact' in ans_type.lower():
            raw_score = self._evaluate_exact(ocr_text, ideal_rubric, grading_mode)
        else:
            raw_score = self._evaluate_flexible(ocr_text, ideal_rubric, grading_mode)
                
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
        
        # Encode rubric sentences and the full student answer (use cache for rubric)
        if ideal_rubric not in self.rubric_sentences_cache:
            self.rubric_sentences_cache[ideal_rubric] = self.embedding_model.encode(rubric_sentences, convert_to_tensor=True)
        rubric_embeddings = self.rubric_sentences_cache[ideal_rubric]
        
        student_embedding = self.embedding_model.encode(student_answer, convert_to_tensor=True)
        
        # Compute cosine similarity of student answer against each rubric sentence
        similarities = util.cos_sim(student_embedding, rubric_embeddings)[0]
        
        # Threshold: rubric points with similarity < 0.35 are considered "missing"
        threshold = 0.35
        raw_missing = [
            rubric_sentences[i]
            for i in range(len(rubric_sentences))
            if similarities[i].item() < threshold
        ]
        
        # Clean each missing point: strip leading stop words / filler so output is technical
        _stop_starts = {
            'a', 'an', 'the', 'it', 'its', 'this', 'that', 'these', 'those',
            'there', 'they', 'he', 'she', 'we', 'you', 'i', 'in', 'is', 'are',
            'was', 'were', 'also', 'each', 'every', 'some', 'any', 'both',
            'such', 'then', 'when', 'where', 'which', 'who', 'how', 'if'
        }
        
        def clean_point(sentence):
            words = sentence.split()
            # Drop leading stop/filler words
            while words and words[0].lower().rstrip(',:') in _stop_starts:
                words = words[1:]
            # Capitalise first word and return
            if not words:
                return sentence.strip()
            words[0] = words[0].capitalize()
            return ' '.join(words)
        
        missing_points = [clean_point(p) for p in raw_missing if clean_point(p)]
        
        # Build the feedback message
        if awarded_marks == max_marks:
            return "All key points from the rubric were addressed."
        
        if not missing_points:
            return "The answer covered most rubric points but lacked depth."
        
        # Format as a clean numbered list of technical phrases
        items = "; ".join(missing_points[:4])
        return f"The following rubric points were not adequately addressed: {items}."

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
        if min_length and str(min_length).lower() != 'none' and grading_mode != 'lenient':
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
