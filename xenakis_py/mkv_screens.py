"""
Screen mappings for Analogique A based on Chapter III of *Formalized Music* by Iannis Xenakis (pages 79–109).

In Xenakis's stochastic composition model, each moment in time is represented by a "screen" — a 2D grid of sound grains defined by three parameters:
- Pitch field (f₀ or f₁): defines the frequency region of the grains
- Intensity field (g₀ or g₁): defines the amplitude (velocity) region
- Density field (d₀ or d₁): defines the number of grains per second

There are 8 possible screen states (A–H), each representing a unique combination of these three binary fields. These screens evolve over time according to a Markovian transition matrix (MTPZ), which defines the probability of moving from one screen to another. The system tends toward a stationary distribution unless perturbed by external forces (P₁, P₂, etc.).

This module maps each screen state to a dictionary of parameters used for stochastic cloud generation:
- pitch_range: (min_midi_note, max_midi_note)
- velocity_range: (min_velocity, max_velocity)
- density: number of events per second
- duration: duration of each screen in seconds (fixed at 1.1 seconds for Analogique A)

These mappings are used by mkv_markov.py and mkv_analogique_a.py to generate MIDI sequences that simulate the evolution of musical textures over time.
"""

from xenakis_py.markov import ScreenState


# Define pitch fields
pitch_fields = {
    "f0": (48, 72),   # C3 to C5
    "f1": (60, 84),   # C4 to C6
}

# Define intensity fields
intensity_fields = {
    "g0": (40, 80),   # softer
    "g1": (80, 120),  # louder
}

# Define density fields
density_fields = {
    "d0": 5,   # sparse
    "d1": 15,  # dense
}

# Duration per screen (from Analogique A)
screen_duration = 1.1  # seconds

# Mapping of screen states to parameter sets
screen_mappings = {
    ScreenState.A: {
        "pitch_range": pitch_fields["f0"],
        "velocity_range": intensity_fields["g0"],
        "density": density_fields["d0"],
        "duration": screen_duration,
    },
    ScreenState.B: {
        "pitch_range": pitch_fields["f0"],
        "velocity_range": intensity_fields["g0"],
        "density": density_fields["d1"],
        "duration": screen_duration,
    },
    ScreenState.C: {
        "pitch_range": pitch_fields["f0"],
        "velocity_range": intensity_fields["g1"],
        "density": density_fields["d0"],
        "duration": screen_duration,
    },
    ScreenState.D: {
        "pitch_range": pitch_fields["f0"],
        "velocity_range": intensity_fields["g1"],
        "density": density_fields["d1"],
        "duration": screen_duration,
    },
    ScreenState.E: {
        "pitch_range": pitch_fields["f1"],
        "velocity_range": intensity_fields["g0"],
        "density": density_fields["d0"],
        "duration": screen_duration,
    },
    ScreenState.F: {
        "pitch_range": pitch_fields["f1"],
        "velocity_range": intensity_fields["g0"],
        "density": density_fields["d1"],
        "duration": screen_duration,
    },
    ScreenState.G: {
        "pitch_range": pitch_fields["f1"],
        "velocity_range": intensity_fields["g1"],
        "density": density_fields["d0"],
        "duration": screen_duration,
    },
    ScreenState.H: {
        "pitch_range": pitch_fields["f1"],
        "velocity_range": intensity_fields["g1"],
        "density": density_fields["d1"],
        "duration": screen_duration,
    },
}

def get_screen_params(state: ScreenState) -> dict:
    """
    Returns the parameter dictionary for a given screen state.

    Args:
        state (ScreenState): One of A–H

    Returns:
        dict: pitch_range, velocity_range, density, duration
    """
    return screen_mappings[state]