import pyttsx3
import threading

engine = None

def get_engine():
    global engine
    if engine is None:
        engine = pyttsx3.init()
        # List available voices (optional)
        voices = engine.getProperty('voices')
        # Try to find a female voice (you can also specify by name)
        female_voice = None
        for voice in voices:
            # Many female voices have "female" in the name or id, or you can pick one manually
            if 'female' in voice.name.lower() or 'zira' in voice.id.lower():  # Windows often has 'Zira' (female)
                female_voice = voice.id
                break
        if female_voice:
            engine.setProperty('voice', female_voice)
        else:
            # Fallback: try to pick a voice that sounds female (you can experiment)
            # On Windows, 'Microsoft Zira Desktop' is female
            for voice in voices:
                if 'zira' in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    break
        engine.setProperty('rate', 170)   # Speed
        engine.setProperty('volume', 0.9) # Volume
    return engine

def speak(text):
    def _speak():
        eng = get_engine()
        eng.say(text)
        eng.runAndWait()
    threading.Thread(target=_speak, daemon=True).start()
