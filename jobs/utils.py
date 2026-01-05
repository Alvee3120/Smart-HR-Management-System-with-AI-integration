import fitz  # PyMuPDF
from django.apps import apps
import re  # Regex for logic
from numpy.linalg import norm
import numpy as np

def extract_text_from_pdf(pdf_file):
    """
    Extracts text using 'Layout Analysis' (Blocks).
    Essential for multi-column Job Descriptions.
    """
    text = ""
    try:
        with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
            for page in doc:
                blocks = page.get_text("blocks")
                # Sort by vertical position (top->bottom), then horizontal (left->right)
                blocks.sort(key=lambda b: (b[1], b[0]))
                for b in blocks:
                    text += b[4] + "\n"
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
    return text

def extract_years_required(text):
    """
    Logic: Looks for patterns like '4+ years', '5-7 years', '3 years'.
    Returns the integer value (e.g., 4). Returns 0 if not found.
    """
    # Regex finds digits followed by "year" (e.g. "4+ years", "4 years")
    # Captures the first digit found associated with 'experience'
    match = re.search(r'(\d+)\+?\s*-?\s*(\d*)?\s+years?\s+of\s+experience', text, re.IGNORECASE)
    
    if not match:
        # Fallback: Try simpler pattern "4+ years" if "of experience" is missing
        match = re.search(r'(\d+)\+?\s*-?\s*(\d*)?\s+years?', text, re.IGNORECASE)
    
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return 0
    return 0

def run_ai_pipeline(job_instance):
    print(f"--- Processing Job: {job_instance.title} ---")

    try:
        JobsConfig = apps.get_app_config('jobs')
        gliner = JobsConfig.gliner_model
        jina = JobsConfig.jina_model
    except LookupError:
        print("⚠️ Jobs app not found.")
        return

    if not gliner or not jina:
        print("⚠️ AI Models not loaded.")
        return

    # 1. Get & Clean Text
    raw_text = job_instance.description_text or ""
    
    if job_instance.description_file:
        try:
            file_text = extract_text_from_pdf(job_instance.description_file)
            if file_text:
                raw_text += "\n" + file_text
            job_instance.description_file.seek(0)
        except Exception as e:
            print(f"⚠️ Failed to process file: {e}")

    # Cleaning: Remove bullets but keep structure
    clean_text = raw_text.replace("•", "").replace("●", "").replace("- ", "")
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    job_instance.processed_text = clean_text

    if not clean_text:
        return

    # 2. GLiNER Extraction
    labels = [
        "Skill", "Technology", "Framework", "Programming Language", 
        "Software", "Tool", "Platform", "Database", "Cloud", "Service",
        "Job Title", "Degree", "Qualification", "Experience"
    ]
    
    try:
        entities = gliner.predict_entities(clean_text, labels, threshold=0.3)
        
        unique_data = []
        seen = set()
        
        # --- LOGIC STEP: EXTRACT YEARS REQUIREMENT ---
        # We calculate this mathematically to ensure accuracy
        req_years = extract_years_required(clean_text)
        if req_years > 0:
            # We add a special system label for the Comparison Logic
            unique_data.append({"label": "Min_Years_Req", "text": str(req_years)})
            print(f"🔢 Logic Found Requirement: {req_years}+ Years")

        for e in entities:
            text = e['text'].strip()
            label = e['label']
            
            # --- FIX 1: FORCE EXPERIENCE RELABELING ---
            # Correct Python syntax: check 'year' OR 'years'
            if "year" in text.lower():
                label = "Experience"

            # --- FIX 2: FORCE AWS/TECH RELABELING ---
            if text.upper() in ["AWS", "AZURE", "GCP", "EC2", "RDS", "LAMBDA", "DOCKER", "KUBERNETES", "GIT", "GITHUB", "LINUX"]:
                if label not in ["Job Title", "Experience"]:
                    label = "Technology"

            key = (label, text.lower())
            if key not in seen:
                seen.add(key)
                unique_data.append({"label": label, "text": text})

        job_instance.gliner_entities = unique_data

    except Exception as e:
        print(f"❌ GLiNER Error: {e}")
        job_instance.gliner_entities = []

    # 3. Jina Embedding
    try:
        embedding = jina.encode(clean_text)
        job_instance.jina_embedding = embedding.tolist()
    except Exception as e:
        print(f"❌ Jina Embedding Error: {e}")

    job_instance.save()
    print("✅ Job Processing Complete.")