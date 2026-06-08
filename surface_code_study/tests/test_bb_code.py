"""
Unit tests for BB code construction.

Verifies:
  - CSS condition H_X · H_Z^T = 0 (mod 2)
  - Code parameters [[n, k]] for [[72,12,6]] and [[144,12,12]]
  - Circulant matrix transpose correctness
  - GF(2) rank computation
  - Polynomial term parsing
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
import pytest

from surface_code_study.qldpc.bb_code import (
    BBCode,
    POLY_A_TERMS,
    POLY_B_TERMS,
    _rank_gf2,
    _kernel_dim_gf2,
    build_bb_code,
    build_bb_code_72_12_6,
    build_bb_code_144_12_12,
    build_circulant_matrix,
    transpose_circulant_matrix,
    _poly_terms_from_string,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Polynomial parsing
# ═══════════════════════════════════════════════════════════════════════════════

def test_poly_parse_a():
    terms = _poly_terms_from_string("x^3 + y + y^2")
    assert sorted(terms) == sorted([(3, 0), (0, 1), (0, 2)])


def test_poly_parse_b():
    terms = _poly_terms_from_string("y^3 + x + x^2")
    assert sorted(terms) == sorted([(0, 3), (1, 0), (2, 0)])


# ═══════════════════════════════════════════════════════════════════════════════
# GF(2) rank
# ═══════════════════════════════════════════════════════════════════════════════

def test_rank_gf2_identity():
    I = np.eye(10, dtype=np.int8)
    assert _rank_gf2(I) == 10


def test_rank_gf2_zero():
    Z = np.zeros((5, 10), dtype=np.int8)
    assert _rank_gf2(Z) == 0


def test_rank_gf2_redundant_rows():
    m = np.array([
        [1, 0, 1],
        [0, 1, 1],
        [1, 1, 0],  # = row0 + row1 mod 2
    ], dtype=np.int8)
    assert _rank_gf2(m) == 2


def test_rank_gf2_hadamard():
    # 3-bit Hamming code check matrix
    H = np.array([
        [1, 1, 1, 0, 1, 0, 0],
        [1, 1, 0, 1, 0, 1, 0],
        [1, 0, 1, 1, 0, 0, 1],
    ], dtype=np.int8)
    assert _rank_gf2(H) == 3


def test_kernel_dim_gf2():
    m = np.eye(5, dtype=np.int8)
    assert _kernel_dim_gf2(m) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Circulant matrix
# ═══════════════════════════════════════════════════════════════════════════════

def test_circulant_shape():
    A = build_circulant_matrix(l=6, m=6, terms=[(3, 0), (0, 1), (0, 2)])
    assert A.shape == (36, 36)


def test_circulant_binary():
    A = build_circulant_matrix(l=6, m=6, terms=[(3, 0), (0, 1), (0, 2)])
    assert np.all((A == 0) | (A == 1))


def test_circulant_each_row_weight():
    # Each row of a circulant matrix built from |terms| terms should have
    # exactly |terms| ones (one per term) unless terms share the same row offset.
    A = build_circulant_matrix(l=6, m=6, terms=[(3, 0), (0, 1), (0, 2)])
    row_weights = np.sum(A, axis=1)
    # The three terms (3,0), (0,1), (0,2) are distinct so each row has weight 3
    assert np.all(row_weights == 3)


def test_circulant_transpose():
    """Verify that numerically computed transpose matches the polynomial transpose."""
    l, m = 6, 6
    terms = [(3, 0), (0, 1), (0, 2)]
    A = build_circulant_matrix(l, m, terms)
    A_T_explicit = A.T
    A_T_via_poly = transpose_circulant_matrix(l, m, terms)
    assert np.array_equal(A_T_explicit, A_T_via_poly)


def test_transpose_is_involution():
    """Transpose of transpose should return to original."""
    l, m = 6, 6
    terms = [(3, 0), (0, 1), (0, 2)]
    A_T = transpose_circulant_matrix(l, m, terms)
    A_TT = transpose_circulant_matrix(l, m,
        [(-di % l, -dj % m) for di, dj in [(3, 0), (0, 1), (0, 2)]])
    A = build_circulant_matrix(l, m, terms)
    assert np.array_equal(A_TT, A)


# ═══════════════════════════════════════════════════════════════════════════════
# CSS condition: H_X · H_Z^T = 0  (mod 2)
# ═══════════════════════════════════════════════════════════════════════════════

def test_css_condition_72_12_6():
    code = build_bb_code_72_12_6()
    assert code.css_ok, "CSS condition failed for [[72,12,6]]"
    product = (code.H_X @ code.H_Z.T) % 2
    assert not np.any(product), f"H_X·H_Z^T has {np.sum(product)} non-zero entries"


def test_css_condition_144_12_12():
    code = build_bb_code_144_12_12()
    assert code.css_ok, "CSS condition failed for [[144,12,12]]"
    product = (code.H_X @ code.H_Z.T) % 2
    assert not np.any(product), f"H_X·H_Z^T has {np.sum(product)} non-zero entries"


# ═══════════════════════════════════════════════════════════════════════════════
# Algebraic proof: A·B + B·A = 0  (mod 2)  →  CSS holds
# ═══════════════════════════════════════════════════════════════════════════════

def test_ab_commutes_mod2():
    """Verify A·B = B·A mod 2 (polynomial multiplication commutes)."""
    l, m = 6, 6
    A = build_circulant_matrix(l, m, POLY_A_TERMS)
    B = build_circulant_matrix(l, m, POLY_B_TERMS)
    AB = (A @ B) % 2
    BA = (B @ A) % 2
    assert np.array_equal(AB, BA), "A·B ≠ B·A — commutativity violated"


# ═══════════════════════════════════════════════════════════════════════════════
# Code parameters (n, k)
# ═══════════════════════════════════════════════════════════════════════════════

def test_72_12_6_n():
    code = build_bb_code_72_12_6()
    assert code.n == 72, f"Expected n=72, got n={code.n}"


def test_72_12_6_k():
    code = build_bb_code_72_12_6()
    assert code.k == 12, f"Expected k=12, got k={code.k}"


def test_144_12_12_n():
    code = build_bb_code_144_12_12()
    assert code.n == 144, f"Expected n=144, got n={code.n}"


def test_144_12_12_k():
    code = build_bb_code_144_12_12()
    assert code.k == 12, f"Expected k=12, got k={code.k}"


# ═══════════════════════════════════════════════════════════════════════════════
# Parametric construction
# ═══════════════════════════════════════════════════════════════════════════════

def test_build_bb_code_generic():
    """Test the generic build_bb_code with custom l, m."""
    for l, m in [(3, 3), (4, 5), (6, 6)]:
        code = build_bb_code(l=l, m=m)
        assert code.n == 2 * l * m
        assert code.css_ok
        assert code.H_X.shape == (l * m, 2 * l * m)
        assert code.H_Z.shape == (l * m, 2 * l * m)


def test_k_nonnegative():
    """Logical qubit count must be non-negative."""
    for l, m in [(3, 3), (4, 4), (6, 6), (12, 6)]:
        code = build_bb_code(l=l, m=m)
        assert code.k >= 0, f"k={code.k} < 0 for l={l}, m={m}"


def test_k_even():
    """k should be even for these symmetric BB constructions."""
    for l, m in [(6, 6), (12, 6)]:
        code = build_bb_code(l=l, m=m)
        assert code.k % 2 == 0, f"k={code.k} is odd for l={l}, m={m}"


# ═══════════════════════════════════════════════════════════════════════════════
# H_X and H_Z structural properties
# ═══════════════════════════════════════════════════════════════════════════════

def test_check_matrices_binary():
    code = build_bb_code_72_12_6()
    assert np.all((code.H_X == 0) | (code.H_X == 1))
    assert np.all((code.H_Z == 0) | (code.H_Z == 1))


def test_each_check_row_nontrivial():
    """Every row of H_X and H_Z must be non-zero (checks must do something)."""
    code = build_bb_code_72_12_6()
    assert np.all(np.sum(code.H_X, axis=1) > 0), "H_X has an all-zero row"
    assert np.all(np.sum(code.H_Z, axis=1) > 0), "H_Z has an all-zero row"


def test_hx_hz_same_rank():
    """H_X and H_Z should have the same rank for these symmetric BB codes."""
    code = build_bb_code_72_12_6()
    assert _rank_gf2(code.H_X) == _rank_gf2(code.H_Z)
    code2 = build_bb_code_144_12_12()
    assert _rank_gf2(code2.H_X) == _rank_gf2(code2.H_Z)


# ═══════════════════════════════════════════════════════════════════════════════
# Edge cases
# ═══════════════════════════════════════════════════════════════════════════════

def test_l1_m1():
    """Smallest possible BB code: l=1, m=1."""
    code = build_bb_code(l=1, m=1)
    assert code.n == 2
    assert code.css_ok


def test_modular_exponent_wrap():
    """Terms with exponents ≥ l or m should wrap correctly."""
    # (6, 0) ≡ (0, 0) mod (6, 6), so should behave like 1+x+x^2 + ...
    A6 = build_circulant_matrix(l=6, m=6, terms=[(6, 0)])
    A0 = build_circulant_matrix(l=6, m=6, terms=[(0, 0)])
    assert np.array_equal(A6, A0)
