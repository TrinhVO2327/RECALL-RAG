"""SM-2 spaced-repetition scheduling algorithm."""

from dataclasses import dataclass

MIN_EASE = 1.3


@dataclass
class ReviewState:
    """A card scheduling state."""

    interval_days: int = 0
    repetitions: int = 0
    ease_factor: float = 2.5

def review(state: ReviewState, grade: int) -> ReviewState:
    """Apply one review with a self-grade of 0-5. Returns the new state."""
    if not 0 <= grade <= 5:
        raise ValueError("Grade must be between 0 and 5.")

    if grade < 3:
         # Failed recall: relearn from the start. Ease is NOT reset —
        # the card remembers it has been difficult.
        repetitions = 0
        interval = 1
    else:
        repetitions = state.repetitions + 1
        if repetitions == 1:
            interval = 1
        elif repetitions == 2:
            interval = 6
        else:
            interval = round(state.interval_days * state.ease_factor)

    # SM-2 ease adjustment: 5 raises, 4 ~neutral, <=3 lowers.
    ease = state.ease_factor + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    ease = max(ease, MIN_EASE)

    return ReviewState(repetitions=repetitions, interval_days=interval, ease_factor=ease)
