import os
import json
import torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, "data", "training_dataset.jsonl")
MODEL_OUTPUT_DIR = os.path.join(BASE_DIR, "models", "grading_model")

# We use DistilBERT because it is fast and runs easily on laptops
MODEL_NAME = "distilbert-base-uncased"

def load_and_preprocess_data():
    """
    Reads the JSONL dataset and formats the context + answer for the model.
    It normalizes the score to be between 0.0 and 1.0 (Regression).
    """
    texts = []
    labels = []
    
    if not os.path.exists(DATASET_PATH):
        print(f"[!] Dataset not found at {DATASET_PATH}. Please generate data first!")
        return None, None
        
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            
            # Format the text so the AI sees the Question, the Rubric, and the Student's Answer
            formatted_text = f"Question: {record['question']} | Rubric: {record['ideal_rubric']} [SEP] Answer: {record['ocr_text']}"
            
            # Normalize the score (e.g. 12/15 becomes 0.8)
            score = float(record['given_score'])
            max_marks = float(record['max_marks'])
            normalized_score = score / max_marks
            
            texts.append(formatted_text)
            labels.append(normalized_score)
            
    return texts, labels

def main():
    print("--- Phase 3: AI Training Pipeline ---")
    
    texts, labels = load_and_preprocess_data()
    if not texts:
        return
        
    print(f"Loaded {len(texts)} graded examples.")
    
    # Split into Train (80%) and Validation (20%)
    train_texts, val_texts, train_labels, val_labels = train_test_split(texts, labels, test_size=0.2, random_state=42)
    
    print("Loading Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    
    # Tokenize the text
    print("Tokenizing data...")
    train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=512)
    val_encodings = tokenizer(val_texts, truncation=True, padding=True, max_length=512)
    
    # Create Hugging Face Dataset objects
    class GradingDataset(torch.utils.data.Dataset):
        def __init__(self, encodings, labels):
            self.encodings = encodings
            self.labels = labels

        def __getitem__(self, idx):
            item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
            # For regression, labels must be float tensors
            item['labels'] = torch.tensor(self.labels[idx], dtype=torch.float)
            return item

        def __len__(self):
            return len(self.labels)
            
    train_dataset = GradingDataset(train_encodings, train_labels)
    val_dataset = GradingDataset(val_encodings, val_labels)
    
    print("Loading Base Model (DistilBERT)...")
    # num_labels=1 tells Hugging Face we are doing Regression (predicting a score, not a category)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=1)
    
    # Training Configuration
    training_args = TrainingArguments(
        output_dir=MODEL_OUTPUT_DIR,
        num_train_epochs=3,              # 3 passes over the dataset
        per_device_train_batch_size=8,   # Process 8 images at a time
        per_device_eval_batch_size=8,
        eval_strategy="epoch",
        logging_dir='./logs',
        logging_steps=10,
        learning_rate=2e-5,
        save_strategy="epoch",
        load_best_model_at_end=True,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset
    )
    
    print("\nStarting Training! This may take a few minutes...")
    trainer.train()
    
    print(f"\nTraining Complete! Saving your custom model to: {MODEL_OUTPUT_DIR}")
    model.save_pretrained(MODEL_OUTPUT_DIR)
    tokenizer.save_pretrained(MODEL_OUTPUT_DIR)
    
    print("Phase 3 Successful! Your local AI is ready for grading.")

if __name__ == "__main__":
    main()
