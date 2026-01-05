import fitz
import numpy as np
import re
from datetime import datetime
from django.apps import apps
from numpy.linalg import norm

# --- 1. DEFINE A SAFETY NET OF KEYWORDS ---
# GLiNER matches context, this matches exact raw text to catch dense lists.
HARD_SKILLS_DB = {
    # Languages
    "python", "java", "c++", "c#", "javascript", "typescript", "php", "ruby", "swift", "kotlin", "go", "rust",
    # Web / Frameworks
    "django", "flask", "fastapi", "react", "angular", "vue", "next.js", "node.js", "spring", "laravel", 
    "asp.net", "rubyonrails", "flutter", "react native",
    # Data / AI
    "numpy", "pandas", "pytorch", "tensorflow", "keras", "scikit-learn", "opencv", "matplotlib", "seaborn", 
    "nltk", "spacy", "huggingface", "llm", "rag", "transformer", "yolo", "chromadb", "langchain", "ollama",
    # DevOps / Tools
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "github", "gitlab", "jenkins", "terraform", "linux", "redis",
    # Databases
    "sql", "mysql", "postgresql", "mongodb", "sqlite", "oracle", "firebase", "elasticsearch"
}

def extract_text_from_pdf(cv_file):
    text = ""
    try:
        with fitz.open(stream=cv_file.read(), filetype="pdf") as doc:
            for page in doc:
                blocks = page.get_text("blocks")
                blocks.sort(key=lambda b: (b[1], b[0]))
                for b in blocks:
                    text += b[4] + "\n"
    except Exception as e:
        print(f"❌ Error reading CV PDF: {e}")
    return text

def calculate_experience_years(text):
    """
    Scans text for date ranges (e.g. Jan 2020 - Present) and calculates total years.
    Handles overlaps.
    """
    date_pattern = r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{4})\s*[-–]\s*(Present|Current|Now|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})'
    
    matches = re.findall(date_pattern, text, re.IGNORECASE)
    intervals = []
    
    for start_month, start_year, end_str in matches:
        try:
            # Parse Start
            start_date = datetime.strptime(f"{start_month[:3]} {start_year}", "%b %Y")
            
            # Parse End
            if end_str.lower() in ['present', 'current', 'now']:
                end_date = datetime.now()
            else:
                # Cleanup end string to match parsing format
                end_str_clean = re.sub(r'[-–]', '', end_str).strip()
                end_parts = end_str_clean.split()
                if len(end_parts) >= 2:
                    end_date = datetime.strptime(f"{end_parts[0][:3]} {end_parts[-1]}", "%b %Y")
                else:
                    continue

            intervals.append((start_date, end_date))
        except Exception:
            continue

    if not intervals:
        return 0.0

    # Merge Overlapping Intervals
    intervals.sort()
    merged = []
    if intervals:
        curr_start, curr_end = intervals[0]
        for next_start, next_end in intervals[1:]:
            if next_start < curr_end: # Overlap
                curr_end = max(curr_end, next_end)
            else:
                merged.append((curr_start, curr_end))
                curr_start, curr_end = next_start, next_end
        merged.append((curr_start, curr_end))

    # Sum total days
    total_days = sum((end - start).days for start, end in merged)
    return round(total_days / 365.25, 1)

def calculate_cosine_similarity(vec_a, vec_b):
    if vec_a is None or vec_b is None: return 0.0
    try:
        a, b = np.array(vec_a), np.array(vec_b)
        if a.size == 0 or b.size == 0 or np.all(a == 0) or np.all(b == 0): return 0.0
        return float(np.dot(a, b) / (norm(a) * norm(b)))
    except: return 0.0

def process_application(application_instance):
    print(f"--- Processing Application ID: {application_instance.id} ---")
    
    try:
        JobsConfig = apps.get_app_config('jobs')
        gliner = JobsConfig.gliner_model
        jina = JobsConfig.jina_model
    except LookupError: return

    if not gliner or not jina: return

    if application_instance.cv_file:
        raw_text = extract_text_from_pdf(application_instance.cv_file)
        application_instance.cv_file.seek(0)
    else: return

    # Cleaning
    clean_text = raw_text.replace("•", "").replace("●", "").replace("|", "")
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    application_instance.cv_text_content = clean_text

    # --- LOGIC 1: CALCULATE EXPERIENCE YEARS ---
    total_years = calculate_experience_years(clean_text)
    print(f"⏱️ Calculated Experience: {total_years} Years")

    # GLiNER Extraction Config
    labels = [
        "Skill", "Technology", "Framework", "Programming Language", 
        "Job Title", "Project", "Degree", "University", 
        "Database", "Tool", "Platform", "Cloud", "Service"
    ]
    
    unique_data = []
    focused_skills = []
    focused_titles = []

    try:
        # 1. AI Extraction (Context Aware)
        entities = gliner.predict_entities(clean_text, labels, threshold=0.3)
        seen = set()
        
        # Add the Calculated Years as a Logic Entity
        unique_data.append({"label": "Total_Years_Calc", "text": str(total_years)})

        # Header detection for context fixes
        idx_projects = clean_text.upper().find("PROJECTS")
        other_headers = ["EXPERIENCE", "EDUCATION", "SKILLS", "SUMMARY"]
        idx_next = len(clean_text)
        if idx_projects != -1:
            for h in other_headers:
                idx = clean_text.upper().find(h)
                if idx > idx_projects: idx_next = min(idx_next, idx)

        for e in entities:
            text, label = e['text'].strip(), e['label']
            start = e.get('start', -1)

            # Context Logic fixes
            if idx_projects != -1 and label == "Job Title" and idx_projects < start < idx_next:
                label = "Project"
            
            if text.upper() in ["AWS", "DOCKER", "KUBERNETES", "GIT", "GITHUB"]:
                if label not in ["Job Title", "Project"]: label = "Technology"

            key = (label, text.lower())
            if key not in seen:
                seen.add(key)
                unique_data.append({"label": label, "text": text})
                
                if label in ["Skill", "Technology", "Framework", "Database", "Tool", "Platform", "Programming Language"]:
                    focused_skills.append(text)
                elif label in ["Job Title"]:
                    focused_titles.append(text)

        # --- 2. KEYWORD SAFETY NET (REGEX FALLBACK) ---
        # Catches skills that exist in text but GLiNER missed due to formatting
        existing_skills_lower = {s.lower() for s in focused_skills}
        text_lower = clean_text.lower()
        
        for skill in HARD_SKILLS_DB:
            # Use regex boundaries \b to ensure we match "Go" but not "Good"
            if skill not in existing_skills_lower:
                if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                    print(f"⚠️ Recovered missing skill via Regex: {skill}")
                    # Add to extracted data so it shows in UI with a special label
                    unique_data.append({"label": "Skill (Detected)", "text": skill.title()})
                    # Add to list used for Jina Embedding
                    focused_skills.append(skill.title())
                    existing_skills_lower.add(skill)

        application_instance.extracted_data = unique_data

    except Exception as e:
        print(f"Extraction Error: {e}")
        application_instance.extracted_data = []

    # Jina Embedding
    # Now includes both AI-found and Regex-recovered skills
    rich_context = f"Role: {', '.join(focused_titles)}. Skills: {', '.join(focused_skills)}. Exp: {total_years} years. Full: {clean_text}"
    
    try:
        application_instance.cv_embedding = jina.encode(rich_context).tolist()
    except: return

    # Scoring
    if application_instance.job.jina_embedding:
        sim = calculate_cosine_similarity(application_instance.cv_embedding, application_instance.job.jina_embedding)
        application_instance.match_score = round(sim * 100, 2)
    
    application_instance.save()