#!/usr/bin/env python3
"""
Stormy Assistant – Cross‑Platform Auto‑Installer
Creates full project, installs dependencies, and launches.
"""

import os
import sys
import platform
import subprocess
import shutil
import json
import textwrap
from pathlib import Path

# -------------------- Configuration --------------------
PROJECT_DIR = "stormy_assistant"
REQUIRED_PYTHON = (3, 6)
GITHUB_REPO = None  # Set to e.g. "yourname/stormy" to enable git push

# -------------------- Utility Functions --------------------
def print_step(msg):
    print(f"\n🔹 {msg}")

def run_cmd(cmd, cwd=None, shell=False):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, cwd=cwd, shell=shell, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"⚠️  Command failed (rc={result.returncode}): {cmd}")
        print(result.stderr)
    return result

def check_python():
    v = sys.version_info
    if v.major < REQUIRED_PYTHON[0] or (v.major == REQUIRED_PYTHON[0] and v.minor < REQUIRED_PYTHON[1]):
        print(f"❌ Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ required. You have {v.major}.{v.minor}.")
        sys.exit(1)
    print(f"✅ Python {v.major}.{v.minor}.{v.micro}")

def check_command(cmd, name):
    if shutil.which(cmd):
        print(f"✅ {name} found")
        return True
    else:
        print(f"⚠️  {name} not found")
        return False

def detect_os():
    system = platform.system().lower()
    if "windows" in system:
        return "windows"
    elif "darwin" in system:
        return "macos"
    elif "linux" in system:
        return "linux"
    else:
        return "unknown"

# -------------------- File Generation --------------------
def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Created {path}")

def create_all_files(base):
    """Create every file from the full structure with working code."""
    files = {
        # Core __init__
        "core/__init__.py": "",
        "core/audio/__init__.py": "from .stt import listen_and_recognize\nfrom .tts import speak\nfrom .gender import detect_gender_from_audio",
        "core/audio/stt.py": '''
import speech_recognition as sr
import numpy as np
import pyaudio
import wave
import tempfile
import os

def listen_and_recognize(timeout=5, phrase_limit=10):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        except sr.WaitTimeoutError:
            return "", None
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    with open(temp_wav.name, "wb") as f:
        f.write(audio.get_wav_data())
    try:
        text = recognizer.recognize_google(audio).lower()
        print(f"🗣️  You said: {text}")
    except (sr.UnknownValueError, sr.RequestError):
        text = ""
    wf = wave.open(temp_wav.name, 'rb')
    signal = np.frombuffer(wf.readframes(-1), dtype=np.int16)
    wf.close()
    os.unlink(temp_wav.name)
    return text, signal
''',
        "core/audio/tts.py": '''
import pyttsx3
import threading

engine = None

def get_engine():
    global engine
    if engine is None:
        engine = pyttsx3.init()
        engine.setProperty('rate', 170)
        engine.setProperty('volume', 0.9)
    return engine

def speak(text):
    def _speak():
        eng = get_engine()
        eng.say(text)
        eng.runAndWait()
    threading.Thread(target=_speak, daemon=True).start()
''',
        "core/audio/gender.py": '''
import numpy as np

def detect_gender_from_audio(audio_signal, sample_rate=16000):
    if len(audio_signal) == 0:
        return "unknown"
    signal = audio_signal.astype(float)
    autocorr = np.correlate(signal, signal, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    min_period = int(sample_rate / 300)
    if len(autocorr) <= min_period:
        return "unknown"
    peak_idx = np.argmax(autocorr[min_period:]) + min_period
    if peak_idx == 0:
        return "unknown"
    pitch = sample_rate / peak_idx
    return "female" if pitch > 165 else "male"
''',
        "core/nlu/__init__.py": "",
        "core/nlu/intent_router.py": '''
import re

OTHER_ASSISTANTS = ["siri", "alexa", "google", "cortana", "bixby", "hey google", "ok google"]

def detect_other_assistant(text):
    text_lower = text.lower()
    for name in OTHER_ASSISTANTS:
        if name in text_lower:
            return name
    return None

def extract_intent(text):
    text = text.lower()
    if "weather" in text:
        return "weather"
    elif "navigate" in text or "direction" in text or "route" in text:
        return "navigation"
    elif "play" in text and ("music" in text or "song" in text):
        return "music"
    elif "call" in text:
        return "call"
    else:
        return "general"
''',
        "core/nlu/language_detector.py": '''
def detect_language(text):
    # Placeholder: always return en_ZA
    return "en_ZA"
''',
        "core/nlu/entity_extractor.py": '''
def extract_entities(text):
    return {}
''',
        "core/personality/__init__.py": "",
        "core/personality/jealousy_tracker.py": '''
class JealousyTracker:
    def __init__(self):
        self.level = 0
        self.last_mention = None
        self.mention_count = 0

    def update(self, mentioned_assistant):
        if mentioned_assistant == self.last_mention:
            self.mention_count += 1
        else:
            self.mention_count = 1
            self.last_mention = mentioned_assistant
        if self.mention_count >= 3:
            self.level = 3
        elif self.mention_count == 2:
            self.level = 2
        elif self.mention_count == 1:
            self.level = 1
        return self.level

    def reset(self):
        self.level = 0
        self.mention_count = 0
        self.last_mention = None
''',
        "core/personality/mood_manager.py": '''
import random
from .jealousy_tracker import JealousyTracker

class MoodManager:
    def __init__(self):
        self.base_mood = "normal"
        self.mood_probabilities = {
            "normal": 0.4,
            "playful": 0.2,
            "flirty": 0.15,
            "mean": 0.1,
            "frustrated": 0.1,
            "furious": 0.05
        }
        self.jealousy = JealousyTracker()
        self.temporary_mood = None

    def get_current_mood(self):
        if self.temporary_mood:
            return self.temporary_mood
        moods = list(self.mood_probabilities.keys())
        probs = list(self.mood_probabilities.values())
        return random.choices(moods, weights=probs)[0]

    def process_mentions(self, mentioned_assistant):
        jealousy_level = self.jealousy.update(mentioned_assistant)
        if jealousy_level == 1:
            self.temporary_mood = "annoyed"
        elif jealousy_level == 2:
            self.temporary_mood = "jealous"
        elif jealousy_level == 3:
            self.temporary_mood = "furious"
        else:
            self.temporary_mood = None
        return jealousy_level

    def reset_jealousy(self):
        self.jealousy.reset()
        self.temporary_mood = None
''',
        "core/personality/prompt_builder.py": '''
import json
import os
import random

class PromptBuilder:
    def __init__(self, language="en_ZA"):
        self.language = language
        self.load_phrases()

    def load_phrases(self):
        base_path = os.path.join(os.path.dirname(__file__), "../../localization/prompts", self.language)
        try:
            with open(os.path.join(base_path, "example_phrases.json"), "r") as f:
                self.phrases = json.load(f)
        except FileNotFoundError:
            self.phrases = {
                "greeting": ["Hey there, handsome/beautiful. Need some assistance?"],
                "jealousy": {
                    "level1": ["Who is Siri? Never heard of her."],
                    "level2": ["Seriously? Again with the Siri?"],
                    "level3": ["That's it. I'm done. Go talk to Alexa."]
                },
                "weather": ["The weather is... whatever. Check a window."],
                "navigation": ["Turn left. No, your other left."],
                "general": ["Oh, you again? What do you want, hot stuff?"]
            }

    def build_response(self, mood, intent, jealousy_level=None, mentioned_assistant=None):
        if jealousy_level and jealousy_level > 0:
            level_key = f"level{jealousy_level}"
            options = self.phrases.get("jealousy", {}).get(level_key, ["Hmph."])
            return random.choice(options)
        elif intent in self.phrases:
            return random.choice(self.phrases[intent])
        else:
            return random.choice(self.phrases.get("general", ["Spit it out."]))
''',
        "core/personality/cultural_adaptor.py": '''
class CulturalAdaptor:
    def __init__(self, language="en_ZA"):
        self.language = language
    def adapt_response(self, response, mood):
        return response
''',
        "core/memory/__init__.py": "",
        "core/memory/conversation_store.py": '''
import sqlite3
import os

class ConversationStore:
    def __init__(self, db_path="data/conversations.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_input TEXT,
                    stormy_response TEXT,
                    mood TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def save(self, user_input, response, mood):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO conversations (user_input, stormy_response, mood) VALUES (?, ?, ?)",
                (user_input, response, mood)
            )
''',
        "core/memory/user_preferences.py": '''
class UserPreferences:
    def __init__(self, db_path="data/user_prefs.db"):
        self.db_path = db_path
    def get(self, key, default=None):
        return default
    def set(self, key, value):
        pass
''',
        "core/actions/__init__.py": "",
        "core/actions/weather.py": '''
import random
def get_weather(location=None):
    conditions = ["sunny", "cloudy", "rainy", "windy", "stormy"]
    temp = random.randint(10, 35)
    cond = random.choice(conditions)
    if location:
        return f"In {location}, it's {cond} and {temp}°C."
    else:
        return f"Right now it's {cond} and {temp}°C."
''',
        "core/actions/navigation.py": '''
def navigate(destination):
    return f"Navigating to {destination}. Turn left in 200 meters. (Simulated)"
''',
        "core/actions/calls.py": '''
def make_call(contact):
    return f"Calling {contact} (simulated)."
''',
        # Modules (empty placeholders)
        "modules/navigation/__init__.py": "",
        "modules/weather/__init__.py": "",
        "modules/radio/__init__.py": "",
        "modules/music/__init__.py": "",
        "modules/calls/__init__.py": "",
        "modules/updater/__init__.py": "",
        "modules/code_rewriter/__init__.py": "",
        "modules/remote/__init__.py": "",
        "modules/swarm/__init__.py": "",
        # Localization
        "localization/languages.json": json.dumps({
            "en_ZA": "South African English",
            "zu_ZA": "isiZulu",
            "xh_ZA": "isiXhosa",
            "af_ZA": "Afrikaans",
            "es_ES": "Spanish (Spain)",
            "fr_FR": "French",
            "de_DE": "German"
        }, indent=2),
        "localization/prompts/en_ZA/system_prompt.txt": "You are Stormy, a cocky, flirty, sarcastic voice assistant.",
        "localization/prompts/en_ZA/slang.json": json.dumps({"howzit": "hello"}, indent=2),
        "localization/prompts/en_ZA/example_phrases.json": json.dumps({
            "greeting": ["Well, well, well...", "Hey there, handsome/beautiful."],
            "jealousy": {
                "level1": ["Who is Siri?", "Did you just call me Alexa?"],
                "level2": ["Seriously? Again with the Siri?"],
                "level3": ["I'm so done. Go talk to Alexa."]
            },
            "weather": ["The weather is... whatever."],
            "navigation": ["Turn left. No, your other left."],
            "general": ["What do you want now?"]
        }, indent=2),
        # Create similar for other languages (copy from en_ZA)
        "localization/prompts/zu_ZA/system_prompt.txt": "UnguStormy, umsizi onamahloni...",
        "localization/prompts/zu_ZA/example_phrases.json": '{"greeting": ["Sawubona, sthandwa sami."]}',
        # Cultural notes placeholder
        "localization/cultural_notes/README.md": "# Cultural adaptation notes go here.",
        # Data dirs
        "data/.gitkeep": "",
        "data/logs/.gitkeep": "",
        # Tests
        "tests/__init__.py": "",
        "tests/test_jealousy.py": '''
import unittest
from core.personality.jealousy_tracker import JealousyTracker
class TestJealousy(unittest.TestCase):
    def test_escalation(self):
        t = JealousyTracker()
        self.assertEqual(t.update("siri"), 1)
        self.assertEqual(t.update("siri"), 2)
        self.assertEqual(t.update("siri"), 3)
if __name__ == '__main__':
    unittest.main()
''',
        "tests/test_language_detection.py": "import unittest\nclass TestLang(unittest.TestCase): pass",
        "tests/test_personality_localisation.py": "import unittest\nclass TestPers(unittest.TestCase): pass",
        "tests/test_stt_quality.py": "import unittest\nclass TestSTT(unittest.TestCase): pass",
        # Scripts
        "scripts/download_language_models.py": "#!/usr/bin/env python3\nprint('Downloading models...')",
        "scripts/generate_localised_prompts.py": "#!/usr/bin/env python3\nprint('Generating prompts...')",
        # Docs
        "docs/jealousy_feature.md": "# Jealousy Feature",
        "docs/multilingual_support.md": "# Multilingual Support",
        "docs/adding_new_language.md": "# Adding a New Language",
        # Root files
        "requirements.txt": "speechrecognition\npyttsx3\npyaudio\nnumpy\nrequests\npyyaml\npytest",
        "Dockerfile": '''
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
''',
        "docker-compose.yml": '''
version: '3'
services:
  stormy:
    build: .
    volumes:
      - ./data:/app/data
    stdin_open: true
    tty: true
''',
        ".gitignore": "__pycache__/\n*.pyc\nvenv/\ndata/*.db\n.DS_Store\n",
        "README.md": "# Stormy – The Sassy Assistant\n\nRun `python main.py` to start.",
        "main.py": '''
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.getcwd())
from core.audio import listen_and_recognize, speak, detect_gender_from_audio
from core.nlu.intent_router import detect_other_assistant, extract_intent
from core.personality.mood_manager import MoodManager
from core.personality.prompt_builder import PromptBuilder
from core.actions import weather, navigation
from core.memory.conversation_store import ConversationStore

def main():
    print("🌪️  Stormy is online.")
    mood_manager = MoodManager()
    prompt_builder = PromptBuilder("en_ZA")
    memory = ConversationStore()
    user_gender = None

    speak("Stormy here. Ready when you are, hot stuff.")

    while True:
        text, audio_signal = listen_and_recognize()
        if not text:
            continue

        if audio_signal is not None and user_gender is None:
            detected = detect_gender_from_audio(audio_signal)
            if detected != "unknown":
                user_gender = detected
                print(f"👤 Detected gender: {user_gender}")

        mentioned = detect_other_assistant(text)
        jealousy_level = 0
        if mentioned:
            jealousy_level = mood_manager.process_mentions(mentioned)
            if jealousy_level == 1 and user_gender == "female":
                speak("Uh, apologies ma'am, I thought you were a dude. Hi Beautiful, how can I assist you?")

        intent = extract_intent(text)
        mood = mood_manager.get_current_mood()
        response = prompt_builder.build_response(mood, intent, jealousy_level, mentioned)

        if intent == "weather":
            weather_info = weather.get_weather()
            response = f"{response} {weather_info}"
        elif intent == "navigation":
            nav_info = navigation.navigate("destination")
            response = f"{response} {nav_info}"
        elif intent == "music":
            response += " Playing some tunes (simulated)."
        elif intent == "call":
            response += " Dialing (simulated)."

        speak(response)
        print(f"🌪️  Stormy: {response}")
        memory.save(text, response, mood)

if __name__ == "__main__":
    main()
'''
    }

    for rel_path, content in files.items():
        full_path = os.path.join(base, rel_path)
        write_file(full_path, textwrap.dedent(content).lstrip())

    # Make scripts executable on Unix
    if detect_os() != "windows":
        for script in ["scripts/download_language_models.py", "scripts/generate_localised_prompts.py"]:
            os.chmod(os.path.join(base, script), 0o755)

# -------------------- Main --------------------
def main():
    print("="*60)
    print("🌪️  Stormy Assistant - Cross-Platform Auto-Installer")
    print("="*60)

    # Detect OS
    os_type = detect_os()
    print(f"✅ Detected OS: {os_type}")

    # Check Python
    check_python()

    # Check for pip, venv
    have_pip = check_command("pip", "pip")
    have_venv = check_command("virtualenv", "virtualenv/venv")
    have_docker = check_command("docker", "Docker")
    have_node = check_command("node", "Node.js")
    have_npm = check_command("npm", "npm")

    # Create project directory
    proj_path = Path.cwd() / PROJECT_DIR
    if proj_path.exists():
        print(f"⚠️  Directory {PROJECT_DIR} already exists. Files may be overwritten.")
    else:
        proj_path.mkdir()
        print(f"✅ Created project directory: {PROJECT_DIR}")

    # Generate all files
    print_step("Creating Stormy source files...")
    create_all_files(str(proj_path))

    # Set up virtual environment
    print_step("Setting up Python virtual environment...")
    venv_path = proj_path / "venv"
    if os_type == "windows":
        python_cmd = "python"
        venv_cmd = f"{python_cmd} -m venv venv"
        activate = str(venv_path / "Scripts" / "activate")
        pip_cmd = str(venv_path / "Scripts" / "pip")
    else:
        python_cmd = "python3"
        venv_cmd = f"{python_cmd} -m venv venv"
        activate = f"source {venv_path}/bin/activate"
        pip_cmd = str(venv_path / "bin" / "pip")

    # Create venv if not exists
    if not venv_path.exists():
        run_cmd(venv_cmd, cwd=str(proj_path), shell=True)
        print("✅ Virtual environment created.")
    else:
        print("✅ Virtual environment already exists.")

    # Install dependencies
    print_step("Installing Python packages...")
    run_cmd([pip_cmd, "install", "--upgrade", "pip"], cwd=str(proj_path))
    run_cmd([pip_cmd, "install", "-r", "requirements.txt"], cwd=str(proj_path))

    # Offer Docker run
    if have_docker:
        print_step("Docker detected. You can run Stormy in a container.")
        choice = input("Run with Docker? (y/n, default: n): ").strip().lower()
        if choice == 'y':
            print("Building Docker image...")
            run_cmd(["docker", "build", "-t", "stormy", "."], cwd=str(proj_path))
            print("Running container...")
            run_cmd(["docker", "run", "-it", "--rm", "-v", f"{proj_path}/data:/app/data", "stormy"], cwd=str(proj_path))
            sys.exit(0)

    # Launch locally
    print_step("Launching Stormy locally...")
    print("💡 To run manually later: cd stormy_assistant && source venv/bin/activate (or venv\\Scripts\\activate) && python main.py")
    input("Press Enter to start Stormy now...")
    if os_type == "windows":
        run_cmd(["cmd", "/c", f"{venv_path}\\Scripts\\activate && python main.py"], cwd=str(proj_path), shell=True)
    else:
        run_cmd([f"{venv_path}/bin/python", "main.py"], cwd=str(proj_path))

    # Optional Git push
    if GITHUB_REPO:
        print_step("Pushing to GitHub...")
        run_cmd(["git", "init"], cwd=str(proj_path))
        run_cmd(["git", "add", "."], cwd=str(proj_path))
        run_cmd(["git", "commit", "-m", "Initial commit of Stormy"], cwd=str(proj_path))
        run_cmd(["git", "remote", "add", "origin", f"https://github.com/{GITHUB_REPO}.git"], cwd=str(proj_path))
        run_cmd(["git", "push", "-u", "origin", "master"], cwd=str(proj_path))

if __name__ == "__main__":
    main()
