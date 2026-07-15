import os
import json
import time
import html
import traceback
import concurrent.futures
import requests
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

import sys
# Make sure we can import core from parent dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ocr_engine import process_pdf, segment_answers_with_gemini
from core.evaluation_engine import HandwrittenEvaluator
from core.scheme_parser import SchemeParser

app = Flask(__name__)

# Config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "data", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize local offline evaluation engine
try:
    evaluator = HandwrittenEvaluator()
except Exception as e:
    print(f"Warning: Could not initialize local evaluator: {e}")
    evaluator = None

scheme_parser = SchemeParser()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/extract', methods=['POST'])
def extract_text():
    if 'scheme' not in request.files or 'student_pdf' not in request.files:
        return jsonify({'error': 'Missing files'}), 400
        
    scheme_file = request.files['scheme']
    student_file = request.files['student_pdf']
    grading_mode = request.form.get('grading_mode', 'experienced')
    
    if scheme_file.filename == '' or student_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    scheme_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(scheme_file.filename))
    student_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(student_file.filename))
    
    scheme_file.save(scheme_path)
    student_file.save(student_path)
    
    try:
        # Step 1: Parse Scheme
        print("Parsing Scheme DOCX...")
        questions = scheme_parser.parse_scheme(scheme_path)
        if not questions:
            return jsonify({'error': 'No questions found in the DOCX scheme. Check formatting.'}), 400
            
        # Step 2: Extract OCR from Student PDF
        print("Extracting OCR from PDF...")
        ocr_text = process_pdf(student_path)
        if ocr_text.startswith("ERROR"):
            return jsonify({'error': ocr_text}), 500
            
        return jsonify({
            'success': True,
            'ocr_text': ocr_text,
            'questions': questions,
            'grading_mode': grading_mode
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluate', methods=['POST'])
def evaluate_exam():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON payload provided'}), 400
            
        ocr_text = data.get('ocr_text')
        questions = data.get('questions')
        grading_mode = data.get('grading_mode', 'experienced')
        exam_max_override = data.get('exam_max_marks')
        
        if not ocr_text or not questions:
            return jsonify({'error': 'Missing ocr_text or questions in payload'}), 400
            
        # Step 3: Segment Answers
        print("Segmenting Answers with Gemini...")
        segmented_answers = segment_answers_with_gemini(ocr_text, questions)
        
        # Step 4: Evaluate each question
        results = [None] * len(questions)
        total_score = 0
        total_max = 0
        
        print("Starting Evaluation Pipeline...")
        
        def evaluate_question(args):
            i, q = args
            q_safe = q.get('question', '...').encode('ascii', 'ignore').decode()
            print(f"Evaluating Q{i+1}: {q_safe}")
            
            q_text = q.get('question', '')
            ideal = q.get('answer', '')
            max_m = int(q.get('max_marks', 10))
            ans_type = q.get('type', 'flexible').lower()
            min_length = q.get('min_length', None)
            
            q_key = str(q.get('id', str(i+1))).strip()
            
            # Robust fuzzy matching for LLM hallucinated keys
            student_ans = segmented_answers.get(q_key)
            if not student_ans:
                student_ans = segmented_answers.get(f"Q{q_key}")
            if not student_ans:
                student_ans = segmented_answers.get(q_key.replace("Q", ""))
            if not student_ans:
                for k, v in segmented_answers.items():
                    if str(k).lower().strip('q') == q_key.lower().strip('q'):
                        student_ans = v
                        break
                        
            student_ans = (student_ans or "").strip()
            
            if not student_ans or len(student_ans) < 5:
                return i, {
                    'q_num': i+1,
                    'question': q_text,
                    'max_marks': max_m,
                    'type': ans_type.upper(),
                    'score': 0,
                    'reasoning': 'The student did not attempt this question.',
                    'match': 0,
                    'penalty': 0,
                    'extracted_answer': 'Not Attempted'
                }, max_m
            
            eval_result = evaluator.evaluate(
                question=q_text,
                ideal_rubric=ideal,
                ocr_text=student_ans,
                max_marks=max_m,
                ans_type=ans_type,
                components=q.get('components', {}),
                min_length=min_length,
                grading_mode=grading_mode
            )
            
            return i, {
                'q_num': i + 1,
                'question': q_text,
                'max_marks': max_m,
                'type': ans_type.upper(),
                'score': eval_result['score'],
                'reasoning': html.escape(eval_result['reasoning']),
                'trace': eval_result.get('trace', []),
                'match': eval_result['match_percentage'],
                'penalty': eval_result['penalty'],
                'extracted_answer': html.escape(student_ans)
            }, max_m
            
        # Process sequentially
        batch_data = []
        for i, q in enumerate(questions):
            idx, res, max_m = evaluate_question((i, q))
            results[idx] = res
            total_score += res['score']
            total_max += max_m
            
            # Prepare data for batched LLaMA reasoning
            batch_data.append({
                "q_num": res['q_num'],
                "question": res['question'],
                "ideal": q.get('answer', ''),
                "student": res.get('extracted_answer', ''),
                "max_marks": res['max_marks'],
                "score": res['score']
            })

        # ==========================================================
        # MASSIVE BATCHING: Generate all reasoning in 1 API call
        # ==========================================================
        print(f"Generating batched LLaMA reasoning for {len(batch_data)} questions...")
        if evaluator:
            batched_reasoning = evaluator.batch_generate_reasoning(batch_data, grading_mode)
            for res in results:
                q_num_str = str(res['q_num'])
                if q_num_str in batched_reasoning:
                    res['reasoning'] = html.escape(batched_reasoning[q_num_str])
            
        # Override total_max if provided via UI
        if exam_max_override and str(exam_max_override).strip():
            try:
                total_max = int(str(exam_max_override).strip())
            except ValueError:
                pass
            
        return jsonify({
            'success': True,
            'total_score': total_score,
            'total_max': total_max,
            'ocr_extracted': ocr_text,
            'results': results
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Start web server on port 5000
    app.run(debug=True, port=5000)
