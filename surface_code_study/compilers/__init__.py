"""
Platform-aware circuit compilers for surface code simulations.

Provides a factory function get_compiler() that returns the appropriate
PlatformCompiler instance for a given hardware platform.
"""

from surface_code_study.compilers.base import PlatformCompiler
from surface_code_study.compilers.superconducting import SuperconductingCompiler
from surface_code_study.compilers.neutral_atom import NeutralAtomCompiler
from surface_code_study.compilers.trapped_ion import TrappedIonCompiler

# ---------------------------------------------------------------------------
# Platform-specific extra parameters (beyond the base noise_params)
# ---------------------------------------------------------------------------

PLATFORM_EXTRA_PARAMS: dict[str, dict] = {
    "superconducting": {
        "t_cycle_ns": 200.0,       # ~200 ns per syndrome round (measurement limited)
    },
    "neutral_atom": {
        "t_move_ns": 200_000.0,    # 200 μs per movement (round-trip, Bluvstein 2024)
        "t_cycle_ns": 800_000.0,   # 800 μs per round (4 batches × 200 μs movement)
        "n_move_batches": 4,
    },
    "trapped_ion": {
        "t_transport_ns": 2_000_000.0,  # 2 ms per transport (Quantinuum H2 ≈ shuttling)
        "t_cycle_ns": 20_000_000.0,     # ~20 ms per round (transport dominated)
        "p_heating": 0.0,               # negligible phonon heating for now
    },
}

# ---------------------------------------------------------------------------
# Compiler class registry
# ---------------------------------------------------------------------------

_COMPILER_REGISTRY: dict[str, type[PlatformCompiler]] = {
    "superconducting": SuperconductingCompiler,
    "neutral_atom":    NeutralAtomCompiler,
    "ion_trap":        TrappedIonCompiler,
}


def get_compiler(
    platform_name: str,
    distance: int,
    noise_params: dict,
) -> PlatformCompiler:
    """
    Factory: return the appropriate PlatformCompiler for the given platform.

    Parameters
    ----------
    platform_name : str
        One of "superconducting", "neutral_atom", "ion_trap".
    distance : int
        Surface code distance d.
    noise_params : dict
        Base noise parameters (from PlatformParams._asdict() or scaled).
        Must contain: p_gate_1q, p_gate_2q, p_meas, p_reset, T1_us, T2_us.

    Returns
    -------
    PlatformCompiler
        Configured compiler instance.
    """
    if platform_name not in _COMPILER_REGISTRY:
        raise KeyError(
            f"Unknown platform {platform_name!r}. "
            f"Available: {list(_COMPILER_REGISTRY)}"
        )

    # Build the compiler-level noise_params dict from the platform-level params
    params = _map_params(platform_name, noise_params)

    cls = _COMPILER_REGISTRY[platform_name]
    return cls(distance=distance, noise_params=params)


def _map_params(platform_name: str, platform_params: dict) -> dict:
    """
    Map from PlatformParams fields to compiler noise_params fields.

    The existing platform params use the naming:
        p_gate_1q, p_gate_2q, p_meas, p_reset, p_idle, T1_us, T2_us

    The compiler expects:
        p_1q, p_2q, p_meas, p_reset, T1_us, T2_us (plus platform extras)
    """
    params = {
        'p_1q': platform_params.get('p_gate_1q', 0.0),
        'p_2q': platform_params.get('p_gate_2q', 0.0),
        'p_meas': platform_params.get('p_meas', 0.0),
        'p_reset': platform_params.get('p_reset', 0.0),
        'T1_us': platform_params.get('T1_us', 100.0),
        'T2_us': platform_params.get('T2_us', 100.0),
    }

    # Add platform-specific extras
    extras = PLATFORM_EXTRA_PARAMS.get(platform_name, {})
    params.update(extras)

    return params
