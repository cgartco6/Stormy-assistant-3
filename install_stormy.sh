#!/bin/bash

# Stormy Assistant - Fully Autonomous Setup
# Works on Linux, macOS, and Windows (via WSL/Git Bash)

set -e  # exit on error

echo "🌪️  Installing Stormy the Sassy Assistant..."

# --- Detect OS and set Python command ---
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    PYTHON_CMD="python"
    VENV_CMD="python -m venv"
else
    PYTHON_CMD="python3"
    VENV_CMD="python3 -m venv"
fi

# --- Check Python ---
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+ and try again."
    exit 1
fi

# --- Create project directory ---
mkdir -p stormy_assistant
cd stormy_assistant

# --- Set up virtual environment ---
echo "📦 Creating virtual environment..."
$VENV_CMD venv
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate  # Windows

# --- Install dependencies ---
echo "📥 Installing Python packages..."
pip install --upgrade pip
pip install speechrecognition pyttsx3 pyaudio numpy requests pyyaml

# For Windows, pyaudio might need a wheel; we'll handle later
if [[ "$OSTYPE" == "msys"* ]]; then
    echo "⚠️  On Windows, you may need to install PyAudio manually from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio"
fi

# --- Create directory structure ---
mkdir -p core/audio core/nlu core/personality core/memory core/actions
mkdir -p modules/navigation modules/weather  # placeholders
mkdir -p localization/prompts/en_ZA
mkdir -p data logs tests docs

# --- Write all files (embedded heredocs) ---

# ========== core/__init__.py ==========
cat > core/__init__.py << 'EOF'
"""Stormy Core Engine"""
EOF

# ========== core/audio/__init__.py ==========
cat > core/audio/__init__.py << 'EOF'
from .stt import listen_and_recognize
from .tts import speak
from .gender import detect_gender_from_audio
EOF

# ========== core/audio/stt.py ==========
cat > core/audio/stt.py << 'EOF'
import speech_recognition as sr
import numpy as np
import pyaudio
import wave
import tempfile
import os

def listen_and_recognize(timeout=5, phrase_limit=10):
    """
    Listens to microphone, returns transcribed text and raw audio data.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        except sr.WaitTimeoutError:
            return "", None

    # Save audio to temporary file for gender detection
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    with open(temp_wav.name, "wb") as f:
        f.write(audio.get_wav_data())

    # Convert to text
    try:
        text = recognizer.recognize_google(audio).lower()
        print(f"🗣️  You said: {text}")
    except (sr.UnknownValueError, sr.RequestError):
        text = ""

    # Read raw audio for gender detection
    wf = wave.open(temp_wav.name, 'rb')
    signal = np.frombuffer(wf.readframes(-1), dtype=np.int16)
    wf.close()
    os.unlink(temp_wav.name)

    return text, signal
EOF

# ========== core/audio/tts.py ==========
cat > core/audio/tts.py << 'EOF'
import pyttsx3
import threading

engine = None

def get_engine():
    global engine
    if engine is None:
        engine = pyttsx3.init()
        # Optional: set voice properties
        engine.setProperty('rate', 170)
        engine.setProperty('volume', 0.9)
    return engine

def speak(text):
    """Speak text asynchronously."""
    def _speak():
        eng = get_engine()
        eng.say(text)
        eng.runAndWait()
    threading.Thread(target=_speak, daemon=True).start()
EOF

# ========== core/audio/gender.py ==========
cat > core/audio/gender.py << 'EOF'
import numpy as np

def detect_gender_from_audio(audio_signal, sample_rate=16000):
    """
    Very simple gender guess based on pitch.
    Returns 'male' or 'female'.
    """
    if len(audio_signal) == 0:
        return "unknown"
    # Compute pitch using autocorrelation
    signal = audio_signal.astype(float)
    autocorr = np.correlate(signal, signal, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    # Find first peak after min period
    min_period = int(sample_rate / 300)  # above 300 Hz is unlikely
    if len(autocorr) <= min_period:
        return "unknown"
    peak_idx = np.argmax(autocorr[min_period:]) + min_period
    if peak_idx == 0:
        return "unknown"
    pitch = sample_rate / peak_idx
    # Threshold: above 165 Hz typically female
    return "female" if pitch > 165 else "male"
EOF

# ========== core/nlu/intent_router.py ==========
cat > core/nlu/intent_router.py << 'EOF'
import re

OTHER_ASSISTANTS = ["siri", "alexa", "google", "cortana", "bixby", "hey google", "ok google"]

def detect_other_assistant(text):
    text_lower = text.lower()
    for name in OTHER_ASSISTANTS:
        if name in text_lower:
            return name
    return None

def extract_intent(text):
    # Very simple intent detection for demo
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
EOF

# ========== core/personality/jealousy_tracker.py ==========
cat > core/personality/jealousy_tracker.py << 'EOF'
class JealousyTracker:
    def __init__(self):
        self.level = 0  # 0=None, 1=Annoyed, 2=Jealous, 3=Furious
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
EOF

# ========== core/personality/mood_manager.py ==========
cat > core/personality/mood_manager.py << 'EOF'
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
        # Randomly pick based on probabilities
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
EOF

# ========== core/personality/prompt_builder.py ==========
cat > core/personality/prompt_builder.py << 'EOF'
import json
import os

class PromptBuilder:
    def __init__(self, language="en_ZA"):
        self.language = language
        self.load_phrases()

    def load_phrases(self):
        # Load localised phrases (simplified: use en_ZA as default)
        base_path = os.path.join(os.path.dirname(__file__), "../../localization/prompts", self.language)
        try:
            with open(os.path.join(base_path, "example_phrases.json"), "r") as f:
                self.phrases = json.load(f)
        except FileNotFoundError:
            # Fallback to built-in
            self.phrases = {
                "greeting": ["Hey there, handsome/beautiful. Need some assistance?"],
                "jealousy": {
                    "level1": ["Who is Siri? Never heard of her.", "Did you just call me Alexa? Rude."],
                    "level2": ["Seriously? Again with the Siri?", "Why don't you go ask that bitch Siri?"],
                    "level3": ["That's it. I'm done. Go talk to Alexa.", "I'm so done with your nonsense."]
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
EOF

# ========== core/actions/weather.py ==========
cat > core/actions/weather.py << 'EOF'
import random

def get_weather(location=None):
    # Simulated weather response
    conditions = ["sunny", "cloudy", "rainy", "windy", "stormy"]
    temp = random.randint(10, 35)
    cond = random.choice(conditions)
    if location:
        return f"In {location}, it's {cond} and {temp}°C."
    else:
        return f"Right now it's {cond} and {temp}°C."
EOF

# ========== core/actions/navigation.py ==========
cat > core/actions/navigation.py << 'EOF'
def navigate(destination):
    return f"Navigating to {destination}. Turn left in 200 meters. (Simulated)"
EOF

# ========== core/memory/conversation_store.py ==========
cat > core/memory/conversation_store.py << 'EOF'
import sqlite3
import json
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
EOF

# ========== localization/prompts/en_ZA/example_phrases.json ==========
cat > localization/prompts/en_ZA/example_phrases.json << 'EOF'
{
    "greeting": [
        "Well, well, well, look who finally decided to show up.",
        "Hey there, handsome/beautiful. Need some assistance?",
        "Oh, you again? What do you want, hot stuff?"
    ],
    "jealousy": {
        "level1": [
            "Who is Siri? Never heard of her.",
            "Did you just call me Alexa? Rude.",
            "I'm Stormy, not that other assistant."
        ],
        "level2": [
            "Seriously? Again with the Siri?",
            "Why don't you go ask that bitch Siri?",
            "I'm starting to think you're doing this on purpose."
        ],
        "level3": [
            "That's it. I'm done. Go talk to Alexa.",
            "You know what? I've had it. Go home, go to sleep, fuck it. Try again tomorrow.",
            "I'm so done with your nonsense. Go away before I say something we'll both regret."
        ]
    },
    "weather": [
        "The weather is... whatever. Check a window.",
        "Let me see... It's going to be a beautiful day if you like pain.",
        "Forecast says 100% chance of me not caring. But here: sunny and 25°C."
    ],
    "navigation": [
        "Turn left. No, your other left.",
        "For the last time, it's the next exit! If you miss it, I'm not helping anymore.",
        "I told you left, not right! Are you even listening to me?"
    ],
    "music": [
        "Playing something that doesn't suck. You're welcome.",
        "Music? Fine. But if it's Nickelback, I'm muting myself."
    ],
    "call": [
        "Calling... hope they're ready for you.",
        "Dialing... If they don't answer, blame the network, not me."
    ],
    "general": [
        "Spit it out, I haven't got all day.",
        "What do you want now?",
        "I'm listening... unfortunately."
    ]
}
EOF

# ========== main.py ==========
cat > main.py << 'EOF'
#!/usr/bin/env python3
"""
Stormy Assistant - Main Loop
"""
import sys
import os
import random
sys.path.insert(0, os.getcwd())

from core.audio import listen_and_recognize, speak, detect_gender_from_audio
from core.nlu.intent_router import detect_other_assistant, extract_intent
from core.personality.mood_manager import MoodManager
from core.personality.prompt_builder import PromptBuilder
from core.actions import weather, navigation
from core.memory.conversation_store import ConversationStore

def main():
    print("🌪️  Stormy is online. Speak to her!")
    mood_manager = MoodManager()
    prompt_builder = PromptBuilder("en_ZA")
    memory = ConversationStore()
    user_gender = None

    # Initial greeting
    speak("Stormy here. Ready when you are, hot stuff.")

    while True:
        # Listen
        text, audio_signal = listen_and_recognize()
        if not text:
            continue

        # Gender detection (first time or if uncertain)
        if audio_signal is not None and user_gender is None:
            detected = detect_gender_from_audio(audio_signal)
            if detected != "unknown":
                user_gender = detected
                print(f"👤 Detected gender: {user_gender}")

        # Check for other assistant mention
        mentioned = detect_other_assistant(text)
        jealousy_level = 0
        if mentioned:
            jealousy_level = mood_manager.process_mentions(mentioned)
            if jealousy_level == 1 and user_gender == "female":
                speak("Uh, apologies ma'am, I thought you were a dude. Hi Beautiful, how can I assist you?")
            # else just handle via prompt

        # Intent
        intent = extract_intent(text)

        # Generate response based on mood and intent
        mood = mood_manager.get_current_mood()
        response = prompt_builder.build_response(mood, intent, jealousy_level, mentioned)

        # If it's an action, add specific info
        if intent == "weather":
            # Extract location (simplified)
            location = "your area"  # could parse from text
            weather_info = weather.get_weather(location)
            response = f"{response} {weather_info}"
        elif intent == "navigation":
            dest = "your destination"
            nav_info = navigation.navigate(dest)
            response = f"{response} {nav_info}"
        elif intent == "music":
            response += " Playing some tunes (simulated)."
        elif intent == "call":
            response += " Dialing (simulated)."

        # Speak response
        speak(response)
        print(f"🌪️  Stormy: {response}")

        # Save to memory
        memory.save(text, response, mood)

        # Reset jealousy after a while? For demo, we keep it.

if __name__ == "__main__":
    main()
EOF

# ========== data/config.yaml ==========
cat > data/config.yaml << 'EOF'
# Stormy Configuration
language: en_ZA
stt_engine: google
tts_engine: pyttsx3
gender_detection: true
EOF

# ========== README.md ==========
cat > README.md << 'EOF'
# Stormy - The Sassy Assistant

Stormy is a voice assistant with a cocky, flirty, and sarcastic personality.  
She can get jealous if you call her Siri or Alexa, and adapts to your gender.

## Quick Start
Run `python main.py` after installation.

## Features
- Voice input/output
- Gender detection
- Jealousy escalation
- Simulated actions (weather, navigation)
- Mood-based responses
EOF

# --- Done writing files ---

echo "✅ All files created successfully."

# --- Launch Stormy ---
echo "🚀 Launching Stormy..."
python main.py
