"""
Analogique A MIDI Generator
---------------------------
Generates a sequence of screen states using MarkovChain (Chapter III, pp. 79–109)
Each screen is rendered as a stochastic cloud of MIDI events using mkv_screens.py mappings.

Output: analogique_a_demo.mid
Duration: ~44 seconds (40 screens × 1.1 sec)
"""

import random
from xenakis_py.markov import MarkovChain, ScreenState
from xenakis_py.mkv_screens import get_screen_params
from xenakis_py.midi_out import MidiRenderer, MidiEvent

# Initialize the Markov chain with default MTPZ matrix
markov_chain = MarkovChain()

# Generate a sequence of screen states
sequence_length = 40  # 40 screens × 1.1 sec ≈ 44 sec
start_state = ScreenState.B
screen_sequence = markov_chain.generate_sequence(start_state, sequence_length)

# Initialize MIDI renderer
renderer = MidiRenderer(tempo=120)

# Generate MIDI events for each screen
current_time = 0.0
for screen_state in screen_sequence:
    params = get_screen_params(screen_state)
    pitch_min, pitch_max = params["pitch_range"]
    vel_min, vel_max = params["velocity_range"]
    density = params["density"]
    duration = params["duration"]

    # Calculate number of events based on density
    num_events = int(density * duration)

    for _ in range(num_events):
        pitch = random.randint(pitch_min, pitch_max)
        velocity = random.randint(vel_min, vel_max)
        start_offset = random.uniform(0, duration)
        event = MidiEvent(
            time=current_time + start_offset,
            pitch=pitch,
            velocity=velocity,
            duration=0.3,
            channel=0
        )
        renderer.add_event(event)

    current_time += duration

# Save the MIDI file
#renderer.save("analogique_a_demo.mid")
#print("✅ MIDI file 'analogique_a_demo.mid' generated successfully.")
if __name__ == "__main__":
    import time

    # Ensure events are sorted before saving (not strictly required, but safe)
    renderer.events.sort(key=lambda e: (e.time, getattr(e, "pitch", 0)))

    # Generate timestamp
    ts = time.strftime("%Y%m%d_%H%M%S")

    # Save with timestamp
    filename = f"analogique_a_demo_{ts}.mid"
    renderer.save(filename)
    print(f"✅ Wrote {filename}")
