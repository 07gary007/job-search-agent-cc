"""Regression tests for the hard score-7 Telegram threshold."""
import unittest
from unittest.mock import patch
import sys
import types

# Keep this regression test offline: main imports the production scraper/scorer,
# whose optional runtime dependencies are not needed to test the score gates.
_jobspy = types.ModuleType("jobspy")
_jobspy.scrape_jobs = lambda **_kwargs: None
sys.modules.setdefault("jobspy", _jobspy)
_anthropic = types.ModuleType("anthropic")
_anthropic.Anthropic = object
sys.modules.setdefault("anthropic", _anthropic)

import main
import notifier


class NotificationThresholdTests(unittest.TestCase):
    def test_main_accepts_only_numeric_scores_from_seven_through_ten(self):
        self.assertTrue(main.is_qualifying_score(7))
        self.assertTrue(main.is_qualifying_score(8.5))
        for value in (6, 6.9999, 0, 11, float("nan"), float("inf"), True, "7", None):
            with self.subTest(value=value):
                self.assertFalse(main.is_qualifying_score(value))

    @patch("notifier.requests.post")
    def test_notifier_never_calls_telegram_for_low_or_invalid_scores(self, post):
        for value in (6, 6.9999, 0, 11, float("nan"), float("inf"), True, "7", None):
            with self.subTest(value=value):
                self.assertFalse(notifier.send_job_notification({}, {"score": value}))
        post.assert_not_called()

    @patch("notifier.requests.post")
    def test_notifier_sends_a_score_of_seven(self, post):
        post.return_value.ok = True
        self.assertTrue(notifier.send_job_notification({"title": "Junior AI Engineer"}, {"score": 7}))
        post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
