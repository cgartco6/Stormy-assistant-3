def test_jealousy_escalation():
    tracker = JealousyTracker()
    assert tracker.update("siri") == 1
    assert tracker.update("siri") == 2
    assert tracker.update("siri") == 3
    assert tracker.update("alexa") == 1  # different assistant resets count
