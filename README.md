 Xenakis2025 – Formalized Music in Python

**Xenakis2025** is a modular Python system for real-time performance and installation, re-implementing the compositional techniques of Iannis Xenakis as described in *Formalized Music* (Pendragon Press, 2001).

## 🎯 Objectives

- Parse and implement Xenakis’s methods:
  - **Sieves** (Ch. XI–XII, pp. 242–267)
  - **Stochastic processes** (Ch. I, VI, XIV, pp. 1–42, 178–200, 277–288)
  - **Markov chains** (Ch. II–III, pp. 43–109)
  - **Dynamic Stochastic Synthesis (DSS)** (Ch. XIII–XIV, pp. 268–288)

- Expose controls via:
  - MIDI (MicroBrute, Model D)
  - OSC (SuperCollider, Csound)
  - Web UI (FastAPI + Dash)

- Package as an interactive app with scene presets for installation or live performance.

## 🧩 Architecture


xenakis_py/
├── xenakis_py/
│   ├── sieve.py          # modulo pitch/rhythm filters
│   ├── stochastic.py     # Poisson, Beta, Gaussian event generation
│   ├── markov.py         # motif/register transitions
│   ├── dss_gendy.py      # DSS via OSC
│   ├── midi_out.py       # MIDI routing
│   ├── osc_bridge.py     # OSC to visuals/lights
│   ├── render.py         # WAV/MIDI export
│   └── scenes/
│       └── default.yaml  # scene preset
├── webui/                # FastAPI + Dash UI
├── scripts/
│   └── demo_sieves_to_midi.py
└── tests/
├── test_sieve.py
└── test_stochastic.py

## ⚙️ Live Setup

- Laptop + Focusrite 18i20 (48 kHz, 128–256 buffer)
- MIDI → MicroBrute (ch1), Model D (ch2)
- OSC → SuperCollider/Csound
- Optional OSC → visuals/lights
- Mixer: Allen & Heath 18-channel desk
- Control surface: Korg NanoKontrol2

## 📚 References

- Iannis Xenakis, *Formalized Music* (Pendragon Press, 2001)
- SuperCollider Gendy UGens
- Csound gendy opcodes
- Smaragdis (1996) on DSS synthesis

## ✅ Definition of Done

- `make demo` plays 3 short pieces (MIDI + WAV)
- Unit tests pass; audio engine stable
- Web UI adjusts parameters live (<10 ms latency)
- Code documented and reproducible
- Scenes exportable for installation or live show