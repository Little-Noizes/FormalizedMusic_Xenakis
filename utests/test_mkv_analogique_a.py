import unittest
import os
from xenakis_py import mkv_analogique_a
from xenakis_py.mkv_screens import ScreenState, get_screen_params

class TestAnalogiqueA(unittest.TestCase):
    def setUp(self):
        # Run the generator to produce the MIDI file
        mkv_analogique_a.renderer.save("analogique_a_demo.mid")

    def test_midi_file_created(self):
        """Check that the MIDI file was created."""
        self.assertTrue(os.path.exists("analogique_a_demo.mid"))

    def test_midi_file_contains_events(self):
        """Ensure the renderer has generated MIDI events."""
        self.assertGreater(len(mkv_analogique_a.renderer.events), 0)

    def test_screen_density_matches_expected(self):
        """Verify that the number of events for a sample screen matches expected density."""
        sample_state = ScreenState.B  # f₀, g₀, d₁ → density = 15
        params = get_screen_params(sample_state)
        expected_density = params["density"]
        duration = params["duration"]
        expected_events = int(expected_density * duration)

        # Count events in the first screen duration
        count = sum(
            1 for event in mkv_analogique_a.renderer.events
            if 0.0 <= event.time < duration
        )
        self.assertEqual(count, expected_events)

    def tearDown(self):
        # Clean up generated MIDI file
        if os.path.exists("analogique_a_demo.mid"):
            os.remove("analogique_a_demo.mid")

if __name__ == "__main__":
    unittest.main()