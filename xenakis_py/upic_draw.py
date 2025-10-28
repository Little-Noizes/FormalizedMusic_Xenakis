"""
UPIC Drawing Interface - Converts drawn shapes to sound parameters
Inspired by Xenakis's UPIC system (Appendix III)
"""

import numpy as np

def convert_path_to_sound(path_points, canvas_width, canvas_height, duration=10.0):
    """
    Convert a list of (x, y) points from the canvas to sound parameters.
    X-axis maps to time, Y-axis maps to frequency.
    Returns a list of (time, frequency) tuples.
    """
    sound_events = []
    for x, y in path_points:
        time = (x / canvas_width) * duration
        frequency = 200 + (y / canvas_height) * 1800  # Map Y to 200Hz–2000Hz
        sound_events.append((time, frequency))
    return sound_events