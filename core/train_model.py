import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        return
        
    client = genai.Client(api_key=api_key)

    print("Loading formatted dataset...")
    with open('data/formatted_tuning_dataset.jsonl', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    examples = []
    for line in lines:
        if not line.strip():
            continue
        data = json.loads(line)
        
        # The new SDK takes text_input and output as strings inside TuningExample
        examples.append(types.TuningExample(
            text_input=data['text_input'],
            output=data['output']
        ))

    print(f"Loaded {len(examples)} examples.")
    print("Starting fine-tuning job on Gemini 1.5 Flash...")

    try:
        # Create the tuning job
        tuning_job = client.tunings.tune(
            base_model='models/gemini-1.5-flash-001-tuning',
            training_dataset=types.TuningDataset(
                examples=examples
            ),
            config=types.CreateTuningJobConfig(
                epoch_count=15, 
                batch_size=4,
                learning_rate_multiplier=1.0,
            )
        )
        
        print(f"Job started! Name: {tuning_job.name}")
        print(f"Base Model: {tuning_job.base_model}")
        print("Waiting for job to complete (this will take roughly 15-30 minutes)...")
        
        # Poll for completion
        while True:
            job = client.tunings.get(name=tuning_job.name)
            state = job.state
            
            # Print timestamped status
            curr_time = time.strftime("%H:%M:%S")
            print(f"[{curr_time}] Current State: {state}")
            
            if state.name in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                 break
            time.sleep(30)
            
        print(f"Final State: {job.state.name}")
        if job.state.name == 'SUCCEEDED':
            tuned_model_id = job.tuned_model.model
            print(f"Tuned Model ID: {tuned_model_id}")
            print("Saving to .env...")
            with open('.env', 'a') as f:
                f.write(f"\nTUNED_MODEL_ID={tuned_model_id}\n")
            print("SUCCESS! Your personalized evaluation model is ready to use.")
        else:
            print("Job did not succeed. Check the Google AI Studio console for more details.")
            
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
