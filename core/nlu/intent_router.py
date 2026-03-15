# Add a list of known assistant names (localised via cultural_adaptor)
OTHER_ASSISTANTS = ["siri", "alexa", "google", "cortana", "bixby", "hey google", "ok google"]

def detect_other_assistant(text):
    text_lower = text.lower()
    for name in OTHER_ASSISTANTS:
        if name in text_lower:
            return name
    return None
