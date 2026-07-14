import json

def convert_to_alpaca():
    input_file = 'data/training_dataset.jsonl'
    output_file = 'data/unsloth_dataset.json'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    dataset = []
    
    for line in lines:
        if not line.strip():
            continue
        data = json.loads(line)
        
        if 'given_score' not in data or 'reasoning' not in data:
            continue
            
        instruction = "Evaluate the following student exam answer based on the provided Ideal Rubric and Max Marks. You MUST output a JSON object containing 'score' and 'reasoning'."
        
        input_text = (
            f"Question: {data.get('question', '')}\n"
            f"Ideal Rubric: {data.get('ideal_rubric', '')}\n"
            f"Max Marks: {data.get('max_marks', '')}\n"
            f"Student Answer (OCR): {data.get('ocr_text', '')}"
        )
        
        output_text = json.dumps({
            "score": str(data.get('given_score', '0')),
            "reasoning": data.get('reasoning', '')
        })
        
        dataset.append({
            "instruction": instruction,
            "input": input_text,
            "output": output_text
        })
        
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=4)
        
    print(f"Created {output_file} with {len(dataset)} examples in Alpaca format.")

if __name__ == "__main__":
    convert_to_alpaca()
