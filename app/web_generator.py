import os
import json
import time
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

import sys
# Make sure we can import core from parent dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ocr_engine import process_pdf
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

@app.route('/api/grade', methods=['POST'])
def grade_exam():
    if 'scheme' not in request.files or 'student_pdf' not in request.files:
        return jsonify({'error': 'Missing files'}), 400
        
    scheme_file = request.files['scheme']
    student_file = request.files['student_pdf']
    
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
            
        # Step 3: Evaluate each question
        results = []
        total_score = 0
        total_max = 0
        
        print("Starting Evaluation Pipeline...")
        for i, q in enumerate(questions):
            q_safe = q.get('question', '...').encode('ascii', 'ignore').decode()
            print(f"Evaluating Q{i+1}: {q_safe}")
            
            q_text = q.get('question', '')
            ideal = q.get('answer', '')
            max_m = q.get('max_marks', 10)
            ans_type = q.get('type', 'flexible')
            min_len = q.get('min_length', None)
            
            eval_result = evaluator.evaluate(
                question=q_text,
                ideal_rubric=ideal,
                max_marks=max_m,
                ocr_text=ocr_text, # passing the entire sheet for simplicity; in prod, you'd segment it
                ans_type=ans_type,
                min_length=min_len
            )
            
            total_score += eval_result['score']
            total_max += max_m
            
            results.append({
                'q_num': i + 1,
                'question': q_text,
                'max_marks': max_m,
                'type': ans_type.upper(),
                'score': eval_result['score'],
                'reasoning': eval_result['reasoning'],
                'match': eval_result['match_percentage'],
                'penalty': eval_result['penalty']
            })
            
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
