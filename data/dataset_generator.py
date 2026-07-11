import os
import glob
import json
import threading
from PIL import Image
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ocr_engine import extract_text_with_gemini

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DatasetGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Handwriting Eval - Dataset Generator (Pro)")
        self.geometry("1400x900")
        
        self.image_paths = []
        self.current_selection = []
        
        self.setup_ui()
        
    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1) # Listbox
        self.grid_columnconfigure(1, weight=3) # Image Viewer
        self.grid_columnconfigure(2, weight=2) # Controls
        self.grid_rowconfigure(0, weight=1)
        
        # --- LEFT FRAME (Listbox) ---
        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        self.left_frame.grid_rowconfigure(2, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)
        
        self.btn_load = ctk.CTkButton(self.left_frame, text="Load Extracted Pages Folder", command=self.load_folder)
        self.btn_load.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.left_frame, text="Hold CTRL to select multiple:", text_color="yellow").grid(row=1, column=0)
        
        self.listbox = tk.Listbox(self.left_frame, selectmode=tk.EXTENDED, bg="#2b2b2b", fg="white", selectbackground="#1f538d", font=("Consolas", 11))
        self.listbox.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        
        # --- MIDDLE FRAME (Image Viewer) ---
        self.middle_frame = ctk.CTkScrollableFrame(self, fg_color="#1a1a1a")
        self.middle_frame.grid(row=0, column=1, padx=5, pady=10, sticky="nsew")
        self.middle_frame.grid_columnconfigure(0, weight=1)
        
        self.image_labels = [] # To hold multiple image labels if they select multiple
        
        # --- RIGHT FRAME (Controls) ---
        self.right_frame = ctk.CTkScrollableFrame(self)
        self.right_frame.grid(row=0, column=2, padx=(5, 10), pady=10, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)
        
        # 1. Context Area
        ctk.CTkLabel(self.right_frame, text="1. Exam Context", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, pady=(10,0), sticky="w", padx=10)
        
        context_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        context_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        context_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(context_frame, text="Question:").grid(row=0, column=0, sticky="w")
        self.txt_question = ctk.CTkTextbox(context_frame, height=60)
        self.txt_question.grid(row=1, column=0, pady=(0,5), sticky="ew")
        
        ctk.CTkLabel(context_frame, text="Ideal Answer / Rubric:").grid(row=2, column=0, sticky="w")
        self.txt_rubric = ctk.CTkTextbox(context_frame, height=80)
        self.txt_rubric.grid(row=3, column=0, sticky="ew")
        
        # 2. AI Extraction Area
        ctk.CTkLabel(self.right_frame, text="2. Handwriting Extraction", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, pady=(15,0), sticky="w", padx=10)
        
        self.btn_extract = ctk.CTkButton(self.right_frame, text="Extract Text (GPT-4o)", command=self.run_ocr_thread)
        self.btn_extract.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        self.lbl_status = ctk.CTkLabel(self.right_frame, text="Ready", text_color="gray")
        self.lbl_status.grid(row=4, column=0, padx=10, sticky="w")
        
        self.txt_ocr = ctk.CTkTextbox(self.right_frame, height=150) # Reduced from 200 so it fits better
        self.txt_ocr.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
        
        # 3. Grading Area
        ctk.CTkLabel(self.right_frame, text="3. Professor's Grade", font=ctk.CTkFont(weight="bold")).grid(row=6, column=0, pady=(15,0), sticky="w", padx=10)
        
        grading_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        grading_frame.grid(row=7, column=0, padx=10, pady=5, sticky="ew")
        grading_frame.grid_columnconfigure(1, weight=1)
        grading_frame.grid_columnconfigure(3, weight=1)
        
        ctk.CTkLabel(grading_frame, text="Max Marks:").grid(row=0, column=0, sticky="w", padx=(0,5))
        self.entry_max = ctk.CTkEntry(grading_frame, placeholder_text="e.g. 5", width=60)
        self.entry_max.grid(row=0, column=1, sticky="w")
        
        ctk.CTkLabel(grading_frame, text="Score Given:").grid(row=0, column=2, sticky="w", padx=(15,5))
        self.entry_score = ctk.CTkEntry(grading_frame, placeholder_text="e.g. 4", width=60)
        self.entry_score.grid(row=0, column=3, sticky="w")
        
        ctk.CTkLabel(self.right_frame, text="Professor's Reasoning:").grid(row=8, column=0, padx=10, sticky="w")
        self.txt_reasoning = ctk.CTkTextbox(self.right_frame, height=60)
        self.txt_reasoning.grid(row=9, column=0, padx=10, pady=5, sticky="ew")
        
        self.btn_save = ctk.CTkButton(self.right_frame, text="SAVE & NEXT", height=40, command=self.save_and_next, fg_color="green", hover_color="darkgreen")
        self.btn_save.grid(row=10, column=0, padx=10, pady=15, sticky="ew")
        
    def load_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder containing images")
        if folder_path:
            exts = ('*.png', '*.jpg', '*.jpeg')
            self.image_paths = []
            for ext in exts:
                self.image_paths.extend(glob.glob(os.path.join(folder_path, ext)))
            self.image_paths.sort()
            
            self.listbox.delete(0, tk.END)
            for path in self.image_paths:
                self.listbox.insert(tk.END, os.path.basename(path))
                
    def on_select(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
            
        self.current_selection = [self.image_paths[i] for i in selection]
        
        # Clear existing image labels
        for lbl in self.image_labels:
            lbl.destroy()
        self.image_labels.clear()
        
        # Render all selected images vertically in the middle frame
        for img_path in self.current_selection:
            try:
                pil_image = Image.open(img_path)
                
                # Calculate new width while maintaining aspect ratio
                target_width = 750
                width_percent = (target_width / float(pil_image.size[0]))
                target_height = int((float(pil_image.size[1]) * float(width_percent)))
                
                ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(target_width, target_height))
                lbl = ctk.CTkLabel(self.middle_frame, image=ctk_img, text="")
                lbl.pack(pady=10)
                self.image_labels.append(lbl)
            except Exception as e:
                lbl = ctk.CTkLabel(self.middle_frame, text=f"Error loading {os.path.basename(img_path)}: {e}")
                lbl.pack(pady=10)
                self.image_labels.append(lbl)
            
    def run_ocr_thread(self):
        if not self.current_selection:
            return
        self.btn_extract.configure(state="disabled")
        self.lbl_status.configure(text=f"Extracting {len(self.current_selection)} pages... (Please wait)", text_color="yellow")
        threading.Thread(target=self._perform_ocr).start()
        
    def _perform_ocr(self):
        try:
            combined_text = ""
            for img_path in self.current_selection:
                pil_image = Image.open(img_path)
                text = extract_text_with_gemini(pil_image)
                combined_text += text + "\n\n---\n\n"
                
            self.after(0, self._update_ocr_text, combined_text)
        except Exception as e:
            self.after(0, self._update_ocr_text, f"ERROR: {str(e)}")
            
    def _update_ocr_text(self, text):
        self.txt_ocr.delete("1.0", tk.END)
        self.txt_ocr.insert("1.0", text)
        self.lbl_status.configure(text="Extraction Complete!", text_color="green")
        self.btn_extract.configure(state="normal")
        
    def save_and_next(self):
        if not self.current_selection:
            messagebox.showwarning("Error", "No images selected!")
            return
            
        ocr_text = self.txt_ocr.get("1.0", tk.END).strip()
        question = self.txt_question.get("1.0", tk.END).strip()
        rubric = self.txt_rubric.get("1.0", tk.END).strip()
        max_marks = self.entry_max.get().strip()
        score = self.entry_score.get().strip()
        
        if not score or not max_marks:
            messagebox.showwarning("Missing Info", "Please enter BOTH Max Marks and Score Given.")
            return
            
        record = {
            "image_paths": self.current_selection,
            "question": question,
            "ideal_rubric": rubric,
            "max_marks": max_marks,
            "ocr_text": ocr_text,
            "given_score": score,
            "reasoning": self.txt_reasoning.get("1.0", tk.END).strip()
        }
        
        out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training_dataset.jsonl")
        with open(out_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
            
        # Select the next un-graded item in the listbox automatically
        last_selected = self.listbox.curselection()[-1]
        if last_selected < self.listbox.size() - 1:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(last_selected + 1)
            self.listbox.see(last_selected + 1)
            self.on_select(None)
            
            # Clear textboxes for next grading (Keep Question/Rubric as they usually stay the same for multiple students)
            self.entry_score.delete(0, tk.END)
            self.txt_reasoning.delete("1.0", tk.END)
            self.txt_ocr.delete("1.0", tk.END)
            self.lbl_status.configure(text="Ready", text_color="gray")

if __name__ == "__main__":
    app = DatasetGeneratorApp()
    app.mainloop()
