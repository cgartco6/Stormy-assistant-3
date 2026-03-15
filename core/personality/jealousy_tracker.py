class JealousyTracker:
    def __init__(self):
        self.level = 0  # 0 = none, 1 = annoyed, 2 = jealous, 3 = furious
        self.last_mention = None
        self.mention_count = 0

    def update(self, mentioned_assistant):
        if mentioned_assistant == self.last_mention:
            self.mention_count += 1
        else:
            self.mention_count = 1
            self.last_mention = mentioned_assistant

        # Escalate level based on count and recency
        if self.mention_count >= 3:
            self.level = 3
        elif self.mention_count == 2:
            self.level = 2
        elif self.mention_count == 1:
            self.level = 1
        return self.level

    def reset(self):
        # Reset after a while or if user apologises
        self.level = 0
        self.mention_count = 0
        self.last_mention = None
