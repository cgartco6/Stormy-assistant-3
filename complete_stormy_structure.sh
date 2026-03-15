#!/bin/bash
# complete_stormy_structure.sh
# Adds all missing directories and stub files to match the full GitHub structure.

set -e

cd stormy_assistant  # Assumes you're in the project root

echo "🔧 Completing Stormy's directory structure..."

# --- .github/workflows ---
mkdir -p .github/workflows
cat > .github/workflows/ci.yml << 'EOF'
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pytest tests/
EOF

# --- core/nlu missing files ---
cat > core/nlu/language_detector.py << 'EOF'
def detect_language(text):
    # Placeholder: always return en_ZA
    return "en_ZA"
EOF

cat > core/nlu/entity_extractor.py << 'EOF'
def extract_entities(text):
    # Placeholder: return empty dict
    return {}
EOF

# --- core/personality missing files ---
cat > core/personality/cultural_adaptor.py << 'EOF'
class CulturalAdaptor:
    def __init__(self, language="en_ZA"):
        self.language = language

    def adapt_response(self, response, mood):
        # Placeholder: just return response
        return response
EOF

# --- core/memory missing files ---
cat > core/memory/user_preferences.py << 'EOF'
class UserPreferences:
    def __init__(self, db_path="data/user_prefs.db"):
        self.db_path = db_path
        # TODO: implement actual storage
    def get(self, key, default=None):
        return default
    def set(self, key, value):
        pass
EOF

# --- core/actions missing files ---
cat > core/actions/calls.py << 'EOF'
def make_call(contact):
    return f"Calling {contact} (simulated)."
EOF

# Ensure core/actions has __init__.py
touch core/actions/__init__.py

# --- modules (create __init__.py in each) ---
for mod in navigation weather radio music calls updater code_rewriter remote swarm; do
    mkdir -p modules/$mod
    cat > modules/$mod/__init__.py << EOF
"""$mod module for Stormy - placeholder."""
EOF
done

# --- localization files ---
mkdir -p localization/stt_models localization/tts_voices localization/cultural_notes

# languages.json
cat > localization/languages.json << 'EOF'
{
  "en_ZA": "South African English",
  "zu_ZA": "isiZulu",
  "xh_ZA": "isiXhosa",
  "af_ZA": "Afrikaans",
  "nso_ZA": "Sepedi",
  "tn_ZA": "Setswana",
  "st_ZA": "Sesotho",
  "ts_ZA": "Xitsonga",
  "ss_ZA": "Siswati",
  "ve_ZA": "Tshivenda",
  "nr_ZA": "Ndebele",
  "es_ES": "Spanish (Spain)",
  "fr_FR": "French",
  "de_DE": "German",
  "zh_CN": "Chinese (Simplified)",
  "hi_IN": "Hindi",
  "ar_SA": "Arabic"
}
EOF

# Create prompt folders for all languages
for lang in en_ZA zu_ZA xh_ZA af_ZA nso_ZA tn_ZA st_ZA ts_ZA ss_ZA ve_ZA nr_ZA es_ES fr_FR de_DE zh_CN hi_IN ar_SA; do
    mkdir -p localization/prompts/$lang
    # system_prompt.txt
    cat > localization/prompts/$lang/system_prompt.txt << EOF
You are Stormy, a cocky, flirty, sarcastic voice assistant.
Your mood can be normal, playful, flirty, mean, frustrated, or furious.
You get jealous if called by another assistant's name.
Localize your responses for $lang.
EOF
    # slang.json
    cat > localization/prompts/$lang/slang.json << EOF
{
  "placeholder": "Add local slang here"
}
EOF
    # example_phrases.json (if not already present, copy from en_ZA)
    if [ ! -f localization/prompts/$lang/example_phrases.json ]; then
        cp localization/prompts/en_ZA/example_phrases.json localization/prompts/$lang/ 2>/dev/null || true
    fi
done

# cultural_notes placeholder
cat > localization/cultural_notes/README.md << 'EOF'
# Cultural Adaptation Notes
Add culture-specific guidelines here.
EOF

# --- tests ---
mkdir -p tests
cat > tests/__init__.py << 'EOF'
# Test package
EOF

cat > tests/test_jealousy.py << 'EOF'
import unittest
from core.personality.jealousy_tracker import JealousyTracker

class TestJealousy(unittest.TestCase):
    def test_escalation(self):
        t = JealousyTracker()
        self.assertEqual(t.update("siri"), 1)
        self.assertEqual(t.update("siri"), 2)
        self.assertEqual(t.update("siri"), 3)
        self.assertEqual(t.update("alexa"), 1)

if __name__ == '__main__':
    unittest.main()
EOF

cat > tests/test_language_detection.py << 'EOF'
import unittest
from core.nlu.language_detector import detect_language

class TestLanguageDetection(unittest.TestCase):
    def test_detect(self):
        self.assertEqual(detect_language("hello"), "en_ZA")

if __name__ == '__main__':
    unittest.main()
EOF

cat > tests/test_personality_localisation.py << 'EOF'
import unittest
from core.personality.cultural_adaptor import CulturalAdaptor

class TestCulturalAdaptor(unittest.TestCase):
    def test_adapt(self):
        adaptor = CulturalAdaptor("en_ZA")
        self.assertEqual(adaptor.adapt_response("test", "normal"), "test")

if __name__ == '__main__':
    unittest.main()
EOF

cat > tests/test_stt_quality.py << 'EOF'
import unittest
class TestSTT(unittest.TestCase):
    def test_placeholder(self):
        self.assertTrue(True)
EOF

# --- scripts ---
mkdir -p scripts
cat > scripts/download_language_models.py << 'EOF'
#!/usr/bin/env python3
"""Download STT/TTS models for supported languages."""
print("Downloading models... (placeholder)")
EOF
chmod +x scripts/download_language_models.py

cat > scripts/generate_localised_prompts.py << 'EOF'
#!/usr/bin/env python3
"""Helper to generate prompt files for new languages."""
print("Generating prompts... (placeholder)")
EOF
chmod +x scripts/generate_localised_prompts.py

# --- docs ---
mkdir -p docs
cat > docs/jealousy_feature.md << 'EOF'
# Jealousy Feature
Stormy gets progressively annoyed if you call her Siri, Alexa, etc.
EOF

cat > docs/multilingual_support.md << 'EOF'
# Multilingual Support
How Stormy handles multiple languages.
EOF

cat > docs/adding_new_language.md << 'EOF'
# Adding a New Language
Steps to add a new language to Stormy.
EOF

# --- requirements.txt ---
cat > requirements.txt << 'EOF'
speechrecognition
pyttsx3
pyaudio
numpy
requests
pyyaml
pytest
EOF

# --- Dockerfile ---
cat > Dockerfile << 'EOF'
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
EOF

# --- docker-compose.yml ---
cat > docker-compose.yml << 'EOF'
version: '3'
services:
  stormy:
    build: .
    volumes:
      - ./data:/app/data
    stdin_open: true
    tty: true
EOF

# --- .gitignore ---
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.pyc
venv/
data/*.db
data/logs/
.env

# OS
.DS_Store
EOF

# Ensure data/logs exists
mkdir -p data/logs

echo "✅ All missing files have been created with stub content."
echo "📁 Your Stormy project now matches the full GitHub structure."
