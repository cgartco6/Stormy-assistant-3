from .jealousy_tracker import JealousyTracker

class MoodManager:
    def __init__(self):
        self.base_mood = "normal"
        self.mood_probabilities = {...}  # existing
        self.jealousy = JealousyTracker()

    def process_mentions(self, mentioned_assistant):
        jealousy_level = self.jealousy.update(mentioned_assistant)
        # Adjust mood based on jealousy level
        if jealousy_level == 1:
            self.temporary_mood = "annoyed"
        elif jealousy_level == 2:
            self.temporary_mood = "jealous"
        elif jealousy_level == 3:
            self.temporary_mood = "furious"
        else:
            self.temporary_mood = None
