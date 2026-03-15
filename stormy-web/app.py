from flask import Flask, render_template, request, jsonify, session
import random
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # for session management

# --- Stormy's core logic (simplified for web) ---
class JealousyTracker:
    def __init__(self):
        self.level = 0
        self.last_mention = None
        self.count = 0

    def update(self, mentioned):
        if mentioned == self.last_mention:
            self.count += 1
        else:
            self.count = 1
            self.last_mention = mentioned
        self.level = min(3, self.count)
        return self.level

    def reset(self):
        self.level = 0
        self.count = 0
        self.last_mention = None

class MoodManager:
    def __init__(self):
        self.moods = ["normal", "playful", "flirty", "mean", "frustrated", "furious"]
        self.weights = [0.4, 0.2, 0.15, 0.1, 0.1, 0.05]
        self.jealousy = JealousyTracker()
        self.temp_mood = None

    def get_mood(self):
        if self.temp_mood:
            return self.temp_mood
        return random.choices(self.moods, weights=self.weights)[0]

    def process_mention(self, mentioned):
        level = self.jealousy.update(mentioned)
        if level == 1:
            self.temp_mood = "annoyed"
        elif level == 2:
            self.temp_mood = "jealous"
        elif level == 3:
            self.temp_mood = "furious"
        else:
            self.temp_mood = None
        return level

# --- Response phrases (localised for English) ---
PHRASES = {
    "greeting": [
        "Well, well, well, look who finally decided to show up.",
        "Hey there, handsome/beautiful. Need some assistance?",
        "Oh, you again? What do you want, hot stuff?"
    ],
    "jealousy": {
        1: ["Who is Siri? Never heard of her.", "Did you just call me Alexa? Rude."],
        2: ["Seriously? Again with the Siri?", "Why don't you go ask that bitch Siri?"],
        3: ["That's it. I'm done. Go talk to Alexa.", "I'm so done with your nonsense."]
    },
    "weather": ["The weather is... whatever. Check a window.", "Let me see... It's going to be a beautiful day if you like pain."],
    "navigation": ["Turn left. No, your other left.", "For the last time, it's the next exit!"],
    "music": ["Playing something that doesn't suck. You're welcome.", "Music? Fine. But if it's Nickelback, I'm muting myself."],
    "call": ["Calling... hope they're ready for you.", "Dialing... If they don't answer, blame the network."],
    "general": ["Spit it out, I haven't got all day.", "What do you want now?"]
}

def get_response(intent, jealousy_level, mentioned, user_gender):
    if jealousy_level > 0:
        return random.choice(PHRASES["jealousy"][jealousy_level])
    elif intent in PHRASES:
        return random.choice(PHRASES[intent])
    else:
        return random.choice(PHRASES["general"])

def extract_intent(text):
    text = text.lower()
    if "weather" in text:
        return "weather"
    elif "navigate" in text or "direction" in text:
        return "navigation"
    elif "play" in text and ("music" in text or "song" in text):
        return "music"
    elif "call" in text:
        return "call"
    else:
        return "general"

def detect_other_assistant(text):
    others = ["siri", "alexa", "google", "cortana", "bixby"]
    for name in others:
        if name in text.lower():
            return name
    return None

# --- Flask routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    user_gender = data.get('gender', 'unknown')

    # Initialize session state for this user
    if 'mood_manager' not in session:
        session['mood_manager'] = {'jealousy': {'level': 0, 'count': 0, 'last': None}}
    # Reconstruct mood manager (simplified)
    mm = MoodManager()
    mm.jealousy.level = session['mood_manager']['jealousy']['level']
    mm.jealousy.count = session['mood_manager']['jealousy']['count']
    mm.jealousy.last_mention = session['mood_manager']['jealousy']['last']

    # Process message
    mentioned = detect_other_assistant(user_message)
    jealousy_level = 0
    if mentioned:
        jealousy_level = mm.process_mention(mentioned)
        # Save back to session
        session['mood_manager']['jealousy']['level'] = mm.jealousy.level
        session['mood_manager']['jealousy']['count'] = mm.jealousy.count
        session['mood_manager']['jealousy']['last'] = mm.jealousy.last_mention
        session.modified = True

    intent = extract_intent(user_message)
    mood = mm.get_mood()
    response = get_response(intent, jealousy_level, mentioned, user_gender)

    # If it's the first time and user_gender known, add misgendering joke
    if jealousy_level == 1 and user_gender == "female" and "apologies" not in response:
        response = "Uh, apologies ma'am, I thought you were a dude. Hi Beautiful, " + response.lower()

    return jsonify({
        'response': response,
        'mood': mood,
        'jealousy_level': jealousy_level
    })

@app.route('/reset_jealousy', methods=['POST'])
def reset_jealousy():
    if 'mood_manager' in session:
        session['mood_manager']['jealousy']['level'] = 0
        session['mood_manager']['jealousy']['count'] = 0
        session['mood_manager']['jealousy']['last'] = None
        session.modified = True
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True)
