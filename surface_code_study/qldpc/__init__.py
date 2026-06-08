"""
qLDPC code constructions and tools.

Currently implements the BB (Bicycle) code family with polynomial-based
check matrix construction, supporting [[72,12,6]] and [[144,12,12]] codes.
"""

from surface_code_study.qldpc.bb_code import BBCode, build_bb_code_72_12_6, build_bb_code_144_12_12
from surface_code_study.qldpc.circuit_builder import (
    build_qldpc_circuit,
    build_qldpc_circuit_from_params,
    build_qldpc_phenomenological_circuit,
)

__all__ = [
    "BBCode",
    "build_bb_code_72_12_6",
    "build_bb_code_144_12_12",
    "build_qldpc_circuit",
    "build_qldpc_circuit_from_params",
    "build_qldpc_phenomenological_circuit",
]
