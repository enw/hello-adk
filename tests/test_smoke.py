import os
import subprocess
import sys
import unittest


class SmokeCommandTests(unittest.TestCase):
    def test_live_calls_require_explicit_opt_in(self):
        result = subprocess.run(
            [sys.executable, "-m", "hello_world.smoke"],
            capture_output=True, text=True, timeout=10,
            env={key: value for key, value in os.environ.items() if key not in {
                "GOOGLE_API_KEY", "GEMINI_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS"
            }},
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--live", result.stderr)
        self.assertIn("may incur API charges", result.stderr)

    def test_session_scenario_requires_opt_in_too(self):
        result = subprocess.run(
            [sys.executable, "-m", "hello_world.smoke", "--scenario", "session"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("may incur API charges", result.stderr)
        self.assertNotIn("unrecognized arguments", result.stderr)
