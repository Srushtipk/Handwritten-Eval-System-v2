import os
import subprocess
import sys

def main():
    gguf_path = input("Drag and drop your .gguf file here and press Enter: ").strip().strip('"').strip("'")
    
    if not os.path.exists(gguf_path):
        print(f"Error: File '{gguf_path}' not found!")
        sys.exit(1)
        
    print("\nCreating Modelfile...")
    with open("Modelfile", "w", encoding='utf-8') as f:
        f.write(f"FROM \"{gguf_path}\"\n")
        
    print("Loading model into Ollama... (this might take a minute)")
    try:
        subprocess.run(["ollama", "create", "my-evaluator", "-f", "Modelfile"], check=True)
        print("\nSUCCESS! Your custom model is now loaded into Ollama.")
        print("You can now run your Evaluation Engine!")
    except FileNotFoundError:
        print("\nERROR: Ollama is not installed or not in your PATH.")
        print("Please download and install Ollama from: https://ollama.com/download/windows")
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Ollama command failed with exit code {e.returncode}")
        print("Make sure the Ollama app is currently running in your system tray!")

if __name__ == "__main__":
    main()
