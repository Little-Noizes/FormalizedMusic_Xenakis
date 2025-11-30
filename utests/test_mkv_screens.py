import unittest
from xenakis_py.mkv_screens import get_screen_params, ScreenState

class TestMKVScreens(unittest.TestCase):
    def test_screen_A_params(self):
        params = get_screen_params(ScreenState.A)
        self.assertEqual(params["pitch_range"], (48, 72))
        self.assertEqual(params["velocity_range"], (40, 80))
        self.assertEqual(params["density"], 5)
        self.assertEqual(params["duration"], 1.1)

    def test_screen_B_params(self):
        params = get_screen_params(ScreenState.B)
        self.assertEqual(params["pitch_range"], (48, 72))
        self.assertEqual(params["velocity_range"], (40, 80))
        self.assertEqual(params["density"], 15)
        self.assertEqual(params["duration"], 1.1)

    def test_screen_C_params(self):
        params = get_screen_params(ScreenState.C)
        self.assertEqual(params["pitch_range"], (48, 72))
        self.assertEqual(params["velocity_range"], (80, 120))
        self.assertEqual(params["density"], 5)
        self.assertEqual(params["duration"], 1.1)

    def test_screen_D_params(self):
        params = get_screen_params(ScreenState.D)
        self.assertEqual(params["pitch_range"], (48, 72))
        self.assertEqual(params["velocity_range"], (80, 120))
        self.assertEqual(params["density"], 15)
        self.assertEqual(params["duration"], 1.1)

    def test_screen_E_params(self):
        params = get_screen_params(ScreenState.E)
        self.assertEqual(params["pitch_range"], (60, 84))
        self.assertEqual(params["velocity_range"], (40, 80))
        self.assertEqual(params["density"], 5)
        self.assertEqual(params["duration"], 1.1)

    def test_screen_F_params(self):
        params = get_screen_params(ScreenState.F)
        self.assertEqual(params["pitch_range"], (60, 84))
        self.assertEqual(params["velocity_range"], (40, 80))
        self.assertEqual(params["density"], 15)
        self.assertEqual(params["duration"], 1.1)

    def test_screen_G_params(self):
        params = get_screen_params(ScreenState.G)
        self.assertEqual(params["pitch_range"], (60, 84))
        self.assertEqual(params["velocity_range"], (80, 120))
        self.assertEqual(params["density"], 5)
        self.assertEqual(params["duration"], 1.1)

    def test_screen_H_params(self):
        params = get_screen_params(ScreenState.H)
        self.assertEqual(params["pitch_range"], (60, 84))
        self.assertEqual(params["velocity_range"], (80, 120))
        self.assertEqual(params["density"], 15)
        self.assertEqual(params["duration"], 1.1)

if __name__ == "__main__":
    unittest.main()