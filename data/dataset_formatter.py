import json

def format_dataset(input_filepath, output_filepath):
    print(f"Reading dataset from {input_filepath}...")
    
    with open(input_filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    formatted_examples = []
    
    for line in lines:
        if not line.strip():
            continue
            
        data = json.loads(line)
        
        # Ensure it's a graded example
        if 'given_score' not in data or 'reasoning' not in data:
            continue
            
        # Construct the text_input precisely as the model will see it in production
        text_input = (
            f"Evaluate the following student answer based on the rubric.\n\n"
            f"Question: {data.get('question', '')}\n"
            f"Ideal Rubric: {data.get('ideal_rubric', '')}\n"
            f"Max Marks: {data.get('max_marks', '')}\n"
            f"Student Answer (OCR Text): {data.get('ocr_text', '')}\n"
        )
        
        # The exact output we want the model to learn to generate
        output = json.dumps({
            "score": str(data.get('given_score', '0')),
            "reasoning": data.get('reasoning', '')
        })
        
        formatted_examples.append({
            "text_input": text_input,
            "output": output
        })
        
    print(f"Formatted {len(formatted_examples)} examples.")
    
    # Save the formatted dataset for reference
    with open(output_filepath, 'w', encoding='utf-8') as f:
        for ex in formatted_examples:
            f.write(json.dumps(ex) + '\n')
            
    print(f"Saved formatted dataset to {output_filepath}")
    return formatted_examples

if __name__ == "__main__":
    format_dataset('data/training_dataset.jsonl', 'data/formatted_tuning_dataset.jsonl')
