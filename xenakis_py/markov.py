"""
Markovian Stochastic Music Engine
---------------------------------
Implements the MarkovChain class and ScreenState enum based on Chapter III of *Formalized Music* by Iannis Xenakis (pp. 79–109).

Each screen state (A–H) represents a unique combination of:
- Pitch field: f₀ or f₁
- Intensity field: g₀ or g₁
- Density field: d₀ or d₁

The MarkovChain class uses an 8×8 transition matrix (MTPZ) to model the evolution of screen states over time.
Includes methods for generating sequences, computing stationary distributions, and applying perturbations.

Reference: Formalized Music, Chapter III, pp. 88–109.
"""

from enum import Enum
import numpy as np

class ScreenState(Enum):
    """Enum representing the 8 screen states (A–H)."""
    A = 0  # f₀, g₀, d₀
    B = 1  # f₀, g₀, d₁
    C = 2  # f₀, g₁, d₀
    D = 3  # f₀, g₁, d₁
    E = 4  # f₁, g₀, d₀
    F = 5  # f₁, g₀, d₁
    G = 6  # f₁, g₁, d₀
    H = 7  # f₁, g₁, d₁

class MarkovChain:
    """
    MarkovChain class for generating screen sequences based on the MTPZ matrix.
    """

    def __init__(self, transition_matrix=None):
        """
        Initialize the MarkovChain with a default or custom transition matrix.
        Default matrix is based on MTPZ from Formalized Music, p. 89.
        """
        if transition_matrix is None:
            matrix = np.array([
                [0.10, 0.05, 0.10, 0.05, 0.10, 0.05, 0.20, 0.30],
                [0.05, 0.10, 0.05, 0.10, 0.05, 0.10, 0.30, 0.25],
                [0.10, 0.05, 0.10, 0.05, 0.10, 0.05, 0.30, 0.25],
                [0.05, 0.10, 0.05, 0.10, 0.05, 0.10, 0.25, 0.30],
                [0.10, 0.05, 0.10, 0.05, 0.10, 0.05, 0.30, 0.25],
                [0.05, 0.10, 0.05, 0.10, 0.05, 0.10, 0.25, 0.30],
                [0.20, 0.30, 0.30, 0.25, 0.30, 0.25, 0.10, 0.05],
                [0.30, 0.25, 0.25, 0.30, 0.25, 0.30, 0.05, 0.10],
            ])
        else:
            matrix = np.array(transition_matrix)

        # Normalize each row to ensure probabilities sum to 1
        self.transition_matrix = matrix / matrix.sum(axis=1, keepdims=True)

    def next_state(self, current_state: ScreenState) -> ScreenState:
        """
        Given the current screen state, return the next state based on transition probabilities.
        """
        probabilities = self.transition_matrix[current_state.value]
        next_index = np.random.choice(range(8), p=probabilities)
        return ScreenState(next_index)

    def generate_sequence(self, start_state: ScreenState, length: int) -> list[ScreenState]:
        """
        Generate a sequence of screen states of given length starting from start_state.
        """
        sequence = [start_state]
        current_state = start_state
        for _ in range(length - 1):
            current_state = self.next_state(current_state)
            sequence.append(current_state)
        return sequence
    def stationary_distribution(self) -> dict[ScreenState, float]:
        """
        Compute the stationary distribution of the Markov chain.
        """
        eigvals, eigvecs = np.linalg.eig(self.transition_matrix.T)
        stat_dist = np.real(eigvecs[:, np.isclose(eigvals, 1)])
        stat_dist = stat_dist[:, 0]
        stat_dist = stat_dist / np.sum(stat_dist)
        return dict(zip(ScreenState, stat_dist))

    def apply_perturbation(self, perturbation_matrix: list[list[float]]) -> None:
        """
        Apply a perturbation matrix to the transition matrix.
        """
        matrix = np.array(perturbation_matrix)
        self.transition_matrix = matrix / matrix.sum(axis=1, keepdims=True)