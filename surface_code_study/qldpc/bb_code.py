"""
BB (Bicycle) code construction from bivariate polynomials.

Given polynomials A(x,y), B(x,y) in F_2[x,y]/(x^l-1, y^m-1), the BB code
has check matrices:

    H_X = [A | B]      (lm × 2lm)
    H_Z = [B^T | A^T]  (lm × 2lm)

where A, B are lm×lm circulant matrices representing multiplication by the
polynomials in the group algebra. The CSS condition H_X·H_Z^T = 0 (mod 2)
is automatically satisfied because polynomial multiplication commutes.

Reference:
    Kovalev & Pryadko, "Quantum LDPC codes from bicycle codes"
    (arXiv:1207.0803)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


# ═══════════════════════════════════════════════════════════════════════════════
# GF(2) linear algebra helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _rank_gf2(matrix: np.ndarray) -> int:
    """Compute the rank of a binary matrix over GF(2) via Gaussian elimination."""
    m = matrix.copy() % 2
    nrows, ncols = m.shape
    rank = 0

    row = 0
    for col in range(ncols):
        if row >= nrows:
            break
        # Find a pivot in this column
        pivot = None
        for r in range(row, nrows):
            if m[r, col]:
                pivot = r
                break
        if pivot is None:
            continue
        # Swap pivot row to current row
        m[[row, pivot]] = m[[pivot, row]]
        # Eliminate all other rows
        for r in range(nrows):
            if r != row and m[r, col]:
                m[r] ^= m[row]
        row += 1
        rank += 1

    return rank


def _kernel_dim_gf2(matrix: np.ndarray) -> int:
    """Compute the dimension of the nullspace over GF(2)."""
    ncols = matrix.shape[1]
    return ncols - _rank_gf2(matrix)


# ═══════════════════════════════════════════════════════════════════════════════
# Polynomial → circulant matrix
# ═══════════════════════════════════════════════════════════════════════════════

def _poly_terms_from_string(poly_str: str) -> List[Tuple[int, int]]:
    """
    Parse a bivariate polynomial string into a list of (i,j) exponent pairs.

    Format examples:
        "x^3 + y + y^2"  →  [(3,0), (0,1), (0,2)]
        "y^3 + x + x^2"  →  [(0,3), (1,0), (2,0)]
        "1 + x + y"       →  [(0,0), (1,0), (0,1)]

    Expects terms separated by '+', each term is x^i y^j or x^i or y^j or 1.
    """
    terms: List[Tuple[int, int]] = []
    for part in poly_str.split("+"):
        part = part.strip()
        if not part:
            continue
        i_exp, j_exp = 0, 0
        if "x" in part:
            if "^" in part[part.index("x"):]:
                # find exponent after x
                x_part = part[part.index("x"):]
                i_exp = int(x_part.split("^")[1].split("y")[0] if "y" in x_part
                           else x_part.split("^")[1])
            else:
                i_exp = 1
        if "y" in part:
            if "^" in part[part.index("y"):]:
                j_exp = int(part[part.index("y"):].split("^")[1])
            else:
                j_exp = 1
        terms.append((i_exp % 256, j_exp % 256))
    return terms


def build_circulant_matrix(
    l: int,
    m: int,
    terms: List[Tuple[int, int]],
) -> np.ndarray:
    """
    Build an lm × lm circulant matrix over GF(2) from polynomial terms.

    The matrix represents multiplication by the polynomial
        p(x,y) = sum_{(i,j) in terms} x^i y^j
    in the group algebra F_2[C_l × C_m].

    Row index (i_out * m + j_out) corresponds to basis element x^{i_out} y^{j_out}.
    Column index (i_in * m + j_in) corresponds to basis element x^{i_in} y^{j_in}.
    The entry A[row, col] = 1 iff x^{row} y^{row_col} appears in p * x^{col} y^{col_col}.

    Parameters
    ----------
    l : int
        Cyclic group size in x (mod x^l = 1).
    m : int
        Cyclic group size in y (mod y^m = 1).
    terms : list of (int, int)
        Exponent pairs (i, j) where the polynomial coefficient is 1.

    Returns
    -------
    np.ndarray of shape (lm, lm), dtype=int8, entries in {0, 1}.
    """
    lm = l * m
    mat = np.zeros((lm, lm), dtype=np.int8)

    for di, dj in terms:
        di_mod = di % l
        dj_mod = dj % m
        for i in range(l):
            i_out = (i + di_mod) % l
            row_base = i_out * m
            col_base = i * m
            for j in range(m):
                j_out = (j + dj_mod) % m
                mat[row_base + j_out, col_base + j] ^= 1

    return mat


def transpose_circulant_matrix(
    l: int,
    m: int,
    terms: List[Tuple[int, int]],
) -> np.ndarray:
    """
    Build the transpose of the circulant matrix for the given polynomial.

    The transpose corresponds to the polynomial with terms (l-di mod l, m-dj mod m).
    """
    transposed_terms = [((-di) % l, (-dj) % m) for di, dj in terms]
    return build_circulant_matrix(l, m, transposed_terms)


# ═══════════════════════════════════════════════════════════════════════════════
# BB Code
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BBCode:
    """
    A BB (Bicycle) quantum LDPC code.

    Attributes
    ----------
    l, m : int
        Cyclic group dimensions. Total qubits n = 2*l*m.
    poly_a_terms : list of (int, int)
        Exponent pairs for polynomial A(x,y).
    poly_b_terms : list of (int, int)
        Exponent pairs for polynomial B(x,y).
    n : int
        Number of physical qubits.
    k : int
        Number of logical qubits (computed via GF(2) rank).
    H_X : np.ndarray
        X-check matrix, shape (lm, 2*lm) over GF(2).
    H_Z : np.ndarray
        Z-check matrix, shape (lm, 2*lm) over GF(2).
    """

    l: int
    m: int
    poly_a_terms: List[Tuple[int, int]]
    poly_b_terms: List[Tuple[int, int]]

    # Computed after __post_init__
    n: int = 0
    k: int = 0
    H_X: np.ndarray | None = None
    H_Z: np.ndarray | None = None
    _css_verified: bool = False

    def __post_init__(self):
        # Build circulant blocks
        A = build_circulant_matrix(self.l, self.m, self.poly_a_terms)
        B = build_circulant_matrix(self.l, self.m, self.poly_b_terms)
        A_T = transpose_circulant_matrix(self.l, self.m, self.poly_a_terms)
        B_T = transpose_circulant_matrix(self.l, self.m, self.poly_b_terms)

        lm = self.l * self.m
        self.n = 2 * lm

        # H_X = [A | B],  H_Z = [B^T | A^T]
        self.H_X = np.hstack([A, B])
        self.H_Z = np.hstack([B_T, A_T])

        # Verify CSS condition: H_X · H_Z^T = 0 (mod 2)
        css_product = (self.H_X @ self.H_Z.T) % 2
        self._css_verified = not np.any(css_product)

        # Compute k = n - rank(H_X) - rank(H_Z)
        r_X = _rank_gf2(self.H_X)
        r_Z = _rank_gf2(self.H_Z)
        self.k = self.n - r_X - r_Z

    @property
    def css_ok(self) -> bool:
        """Whether the CSS condition H_X·H_Z^T = 0 is satisfied."""
        return self._css_verified

    @property
    def code_params(self) -> tuple:
        """Return (n, k) — note: d requires distance computation."""
        return (self.n, self.k)

    @property
    def lm(self) -> int:
        return self.l * self.m

    def summary(self) -> str:
        return (
            f"BBCode(l={self.l}, m={self.m}, n={self.n}, k={self.k}, "
            f"css_ok={self._css_verified})"
        )

    def __repr__(self) -> str:
        return self.summary()


# ═══════════════════════════════════════════════════════════════════════════════
# Known code constructions
# ═══════════════════════════════════════════════════════════════════════════════

# Polynomials for the BB code family (Kovalev-Pryadko style)
# A(x,y) = x^3 + y + y^2
POLY_A_TERMS: List[Tuple[int, int]] = [(3, 0), (0, 1), (0, 2)]

# B(x,y) = y^3 + x + x^2
POLY_B_TERMS: List[Tuple[int, int]] = [(0, 3), (1, 0), (2, 0)]


def build_bb_code(l: int, m: int) -> BBCode:
    """
    Build a BB code with the standard A=x^3+y+y^2, B=y^3+x+x^2 polynomials.

    Parameters
    ----------
    l, m : int
        Cyclic group dimensions. Total qubits = 2*l*m.

    Returns
    -------
    BBCode
    """
    return BBCode(l=l, m=m, poly_a_terms=POLY_A_TERMS, poly_b_terms=POLY_B_TERMS)


def build_bb_code_72_12_6() -> BBCode:
    """Build the [[72, 12, 6]] BB code (l=6, m=6)."""
    return build_bb_code(l=6, m=6)


def build_bb_code_144_12_12() -> BBCode:
    """Build the [[144, 12, 12]] BB code (l=12, m=6)."""
    return build_bb_code(l=12, m=6)


# ═══════════════════════════════════════════════════════════════════════════════
# Quick sanity check
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=== BB Code Construction Sanity Check ===\n")

    for name, code in [
        ("[[72,12,6]]  (l=6, m=6)", build_bb_code_72_12_6()),
        ("[[144,12,12]] (l=12,m=6)", build_bb_code_144_12_12()),
    ]:
        print(f"{name}:")
        print(f"  n={code.n}, k={code.k}, lm={code.lm}")
        print(f"  CSS condition: {'PASS' if code.css_ok else 'FAIL'}")
        print(f"  H_X shape: {code.H_X.shape}")
        print(f"  H_Z shape: {code.H_Z.shape}")
        print(f"  rank(H_X)={_rank_gf2(code.H_X)}")
        print(f"  rank(H_Z)={_rank_gf2(code.H_Z)}")
        print()
