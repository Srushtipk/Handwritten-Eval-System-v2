import re

def resolve_eval_engine():
    with open('core/evaluation_engine.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We will replace the whole conflict block with our merged code
    pattern = re.compile(r'<<<<<<< HEAD.*?=======(.*?)>>>>>>> [a-f0-9]+', re.DOTALL)
    
    merged = r'''        # 1. Semantic Similarity
        semantic_score = cosine_scores[0][0].item()
        
        # 2. Keyword Overlap Score (Factual Precision)
        ideal_words = set(re.findall(r'\b\w{4,}\b', ideal_answer.lower()))
        student_words = set(re.findall(r'\b\w{4,}\b', student_answer.lower()))
        if not ideal_words:
            keyword_score = 1.0
        else:
            matches = ideal_words.intersection(student_words)
            keyword_score = len(matches) / len(ideal_words)
            
        # 3. True Hybrid Calculation
        raw_score = (semantic_score * 0.5) + (keyword_score * 0.5)
        
        # Median Strictness Normalization Mapping:
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
        student_word_list = re.findall(r'\b\w+\b', student_answer.lower())
        ideal_word_list = re.findall(r'\b\w+\b', ideal_answer.lower())
        
        if len(ideal_word_list) > 10 and grading_mode != 'lenient':
            target_length = max(8, int(len(ideal_word_list) * 0.65))
            length_ratio = len(student_word_list) / target_length
            completeness_factor = min(1.0, length_ratio)
            completeness_factor = 0.2 + 0.8 * completeness_factor
            normalized_score = normalized_score * completeness_factor
            
        return normalized_score'''
    
    def repl(m): return merged
    content = pattern.sub(repl, content)
    with open('core/evaluation_engine.py', 'w', encoding='utf-8') as f:
        f.write(content)

def resolve_index():
    with open('app/templates/index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = re.compile(r'<<<<<<< HEAD.*?=======(.*?)>>>>>>> [a-f0-9]+', re.DOTALL)
    
    def repl(m): return m.group(1)
    content = pattern.sub(repl, content)
    with open('app/templates/index.html', 'w', encoding='utf-8') as f:
        f.write(content)

resolve_eval_engine()
resolve_index()
print("Resolved conflicts.")
