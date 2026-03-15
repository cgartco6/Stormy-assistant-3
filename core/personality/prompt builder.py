def build_prompt(user_input, mood_manager, history, language):
    base_prompt = load_localised_prompt(language)  # from localization/
    jealousy_level = mood_manager.jealousy.level
    if jealousy_level > 0:
        jealousy_note = f"\nThe user just called you {mood_manager.jealousy.last_mention}. You are jealous and annoyed. Escalate appropriately."
    else:
        jealousy_note = ""
    # ... rest of prompt building
