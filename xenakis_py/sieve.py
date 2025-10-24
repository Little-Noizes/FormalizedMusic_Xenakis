"""
Module: sieve.py

Implements Xenakis's sieve theory using modular arithmetic to filter pitch or rhythm values
based on logical combinations of modulo clauses.

Each clause is a tuple of (operation, {modulus: int, residues: List[int]}).
Supported operations: 'union', 'intersection', 'complement'.

Shift acts as a metabola: membership is tested on (x − shift) mod m, returning x unchanged.

References:
- Iannis Xenakis, Formalized Music, Chapters XI–XII, pp. 242–267.
"""

import math
from typing import List, Tuple, Dict, Union

class Sieve:
    def __init__(self, clauses: List[Tuple[str, Dict[str, Union[int, List[int]]]]]):
        """
        Initialize the sieve with a list of clauses.

        Parameters:
        - clauses: List of tuples (operation, {modulus: int, residues: List[int]})
        """
        self.clauses = []
        self.shift_amount = 0

        for op, clause in clauses:
            modulus = clause.get('modulus')
            residues = clause.get('residues', [clause.get('residue')])

            if not isinstance(modulus, int) or modulus < 2:
                raise ValueError(f"Invalid modulus: {modulus}. Must be integer ≥ 2.")

            # Normalize residues to 0…m−1, remove None and duplicates
            normalized = sorted(set(r % modulus for r in residues if r is not None))
            if not normalized:
                raise ValueError(f"Residue list for modulus {modulus} is empty after normalization.")

            self.clauses.append((op, {'modulus': modulus, 'residues': normalized}))

    def generate(self, start: int, end: int) -> List[int]:
        """
        Generate a list of integers in the range [start, end] that satisfy the sieve.

        Membership is tested on (x − shift) mod m, returning x unchanged.

        Parameters:
        - start: Start of the range (inclusive)
        - end: End of the range (inclusive)

        Returns:
        - List of integers satisfying the sieve
        """
        universe = set(range(start, end + 1))
        result_set = set()

        for op, clause in self.clauses:
            modulus = clause['modulus']
            residues = clause['residues']
            filtered = {x for x in universe if ((x - self.shift_amount) % modulus) in residues}

            if op == 'union':
                result_set |= filtered
            elif op == 'intersection':
                result_set = filtered if not result_set else (result_set & filtered)
            elif op == 'complement':
                result_set = universe - filtered if not result_set else result_set - filtered

        return sorted(result_set)

    def period(self) -> int:
        """
        Compute the period of the sieve, defined as the least common multiple (LCM)
        of all moduli used in the clauses.

        Returns:
        - Integer period of the sieve
        """
        moduli = [clause['modulus'] for _, clause in self.clauses]
        return math.lcm(*moduli)

    def shift(self, amount: int):
        """
        Shift the sieve test by a fixed amount (metabola).

        Parameters:
        - amount: Integer value to shift the test (not the result)
        """
        self.shift_amount = amount