import pytest

from app.scheduler import MIN_EASE, ReviewState, review


def test_first_two_successes_are_1_then_6_days():
    s = review(ReviewState(), grade=4)
    assert (s.repetitions, s.interval_days) == (1, 1)
    s = review(s, grade=4)
    assert (s.repetitions, s.interval_days) == (2, 6)


def test_third_success_multiplies_by_ease():
    s = ReviewState(repetitions=2, interval_days=6, ease_factor=2.5)
    s = review(s, grade=4)
    assert s.interval_days == 15  # round(6 * 2.5)


def test_failure_resets_schedule_but_keeps_lowered_ease():
    s = ReviewState(repetitions=5, interval_days=90, ease_factor=2.5)
    s = review(s, grade=1)
    assert (s.repetitions, s.interval_days) == (0, 1)
    assert s.ease_factor < 2.5  # difficulty is remembered


def test_ease_never_drops_below_floor():
    s = ReviewState(ease_factor=1.3)
    for _ in range(10):
        s = review(s, grade=0)
    assert s.ease_factor == MIN_EASE


def test_grade_5_raises_ease():
    s = review(ReviewState(), grade=5)
    assert s.ease_factor > 2.5


def test_invalid_grade_raises():
    with pytest.raises(ValueError):
        review(ReviewState(), grade=6)

        