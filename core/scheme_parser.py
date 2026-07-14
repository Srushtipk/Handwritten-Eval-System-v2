import docx
import re

class SchemeParser:
    def __init__(self):
        pass
        
    def parse_scheme(self, docx_path):
        """
        Parses a DOCX marking scheme and returns a list of question dictionaries.
        Expected format:
        Question: ...
        Max Marks: ...
        Type: Flexible/Exact
        Min Length: ... (optional)
        Answer: ...
        """
        doc = docx.Document(docx_path)
        
        questions = []
        current_question = {}
        
        # We will iterate through paragraphs and extract fields
        # Using a simple state machine approach
        
        current_key = None
        current_value = ""
        
        def save_field():
            nonlocal current_key, current_value, current_question
            if current_key:
                val = current_value.strip()
                if current_key == 'question':
                    current_question['question'] = val
                elif current_key == 'max_marks':
                    # Extract numbers
                    nums = re.findall(r'\d+', val)
                    if nums:
                        current_question['max_marks'] = int(nums[0])
                elif current_key == 'type':
                    current_question['type'] = val.lower()
                elif current_key == 'min_length':
                    current_question['min_length'] = val
                elif current_key == 'answer':
                    current_question['answer'] = val
            
        for para in doc.paragraphs:
            text_block = para.text.strip()
            if not text_block:
                continue
                
            # Handle soft-returns (Shift+Enter) within a single paragraph
            for text in text_block.split('\n'):
                text = text.strip()
                if not text:
                    continue
                    
                # Check for headers
                if text.lower().startswith("question:"):
                    save_field()
                    if 'question' in current_question and 'answer' in current_question:
                        questions.append(current_question)
                    current_question = {}
                    
                    current_key = 'question'
                    current_value = text[len("question:"):].strip() + "\n"
                    
                elif text.lower().startswith("max marks:"):
                    save_field()
                    current_key = 'max_marks'
                    current_value = text[len("max marks:"):].strip() + "\n"
                    
                elif text.lower().startswith("type:"):
                    save_field()
                    current_key = 'type'
                    current_value = text[len("type:"):].strip() + "\n"
                    
                elif text.lower().startswith("min length:"):
                    save_field()
                    current_key = 'min_length'
                    current_value = text[len("min length:"):].strip() + "\n"
                    
                elif text.lower().startswith("answer:"):
                    save_field()
                    current_key = 'answer'
                    current_value = text[len("answer:"):].strip() + "\n"
                else:
                    # Append to current value if it's a multi-line field
                    if current_key:
                        current_value += text + "\n"
                    
        # Save the last field and question
        save_field()
        if 'question' in current_question and 'answer' in current_question:
            questions.append(current_question)
            
        return questions

if __name__ == "__main__":
    # Test script will be run by passing a dummy docx
    pass
