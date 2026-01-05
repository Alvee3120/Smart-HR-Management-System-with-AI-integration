from django.apps import AppConfig
from gliner import GLiNER
from sentence_transformers import SentenceTransformer
import os
from django.conf import settings

class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'

    gliner_model = None
    jina_model = None

    def ready(self):
        if os.environ.get('RUN_MAIN') == 'true':
            print("🧠 Loading AI Models...")
            
            # 1. Load GLiNER (Downloads automatically if not present)
            self.gliner_model = GLiNER.from_pretrained("urchade/gliner_small-v2.1")
            
            # 2. Load Your Local Fine-Tuned Jina Model
            # We construct the absolute path to your model folder
            model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'my_finetuned_jina')
            
            if os.path.exists(model_path):
                self.jina_model = SentenceTransformer(model_path, trust_remote_code=True)
                print(f"✅ Loaded Jina Model from: {model_path}")
            else:
                print(f"❌ Model not found at {model_path}. Did you unzip it there?")
