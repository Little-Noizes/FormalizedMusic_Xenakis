
import math
import pytest
from xenakis_py.sieve import Sieve


def test_multi_residues_union():
    # keep numbers that are 0 OR 2 mod 5
    s = Sieve([("union", {"modulus": 5, "residues": [0, 2]})])
    r = s.generate(0, 30)
    exp = sorted([x for x in range(31) if x % 5 in (0,2)])
    assert r == exp

def test_shift_metabola_preserves_window():
    # numbers 1 mod 6, but shift by +2 means we accept x such that (x-2) % 6 == 1 -> x % 6 == 3
    s = Sieve([("union", {"modulus": 6, "residues": [1]})])
    s.shift(2)
    r = s.generate(0, 25)
    exp = [x for x in range(26) if x % 6 == 3]
    assert r == exp
    # ensure results stay within requested range
    assert all(0 <= x <= 25 for x in r)

def test_complement_against_universe_if_first():
    # Start with complement of multiples of 4 -> universe minus those
    s = Sieve([("complement", {"modulus": 4, "residues": [0]})])
    r = s.generate(0, 20)
    exp = [x for x in range(21) if x % 4 != 0]
    assert r == exp

def test_intersection_then_complement():
    clauses = [
        ("intersection", {"modulus": 7, "residues": [2]}),
        ("intersection", {"modulus": 5, "residues": [2]}),
        ("complement",   {"modulus": 3, "residues": [2]}),
    ]
    s = Sieve(clauses)
    u = range(0, 140)
    exp = [x for x in u if (x % 7 == 2 and x % 5 == 2) and not (x % 3 == 2)]
    assert s.generate(0, 139) == exp

def test_residue_normalisation_and_validation():
    # negative residues and duplicates should be normalised and deduped
    s = Sieve([("union", {"modulus": 8, "residues": [-1, 7, 15, 7]})])  # -> {7}
    assert s.generate(0, 25) == [7, 15, 23]
    # empty residues list after normalisation should error
    with pytest.raises(ValueError):
        Sieve([("union", {"modulus": 5, "residues": []})])

def test_period_is_lcm_of_moduli():
    s = Sieve([("union", {"modulus": 4, "residues": [1]}),
               ("intersection", {"modulus": 6, "residues": [5]}),
               ("union", {"modulus": 7, "residues": [0]})])
    assert s.period() == math.lcm(4,6,7)
