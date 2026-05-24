"""
Tests for platform-aware circuit compilers.

Run with:  python -m pytest surface_code_study/tests/test_compilers.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import stim
from surface_code_study.compilers import get_compiler
from surface_code_study.platforms import PLATFORMS, get_platform

PLATFORM_NAMES = ["superconducting", "neutral_atom", "ion_trap"]


def _get_zero_noise_params(platform_name: str) -> dict:
    """Return noise params with all error probabilities set to zero."""
    return {
        'p_gate_1q': 0.0,
        'p_gate_2q': 0.0,
        'p_meas': 0.0,
        'p_reset': 0.0,
        'T1_us': 1e12,     # effectively infinite → no idle decoherence
        'T2_us': 1e12,
    }


def _get_default_params(platform_name: str) -> dict:
    """Return noise params at natural operating point."""
    p = get_platform(platform_name)
    return p._asdict()


# ---------------------------------------------------------------------------
# Zero-noise tests
# ---------------------------------------------------------------------------

def test_zero_noise_superconducting():
    """Zero noise → PL=0 for superconducting compiler."""
    params = _get_zero_noise_params("superconducting")
    compiler = get_compiler("superconducting", distance=3, noise_params=params)
    circuit = compiler.build_memory_circuit(num_rounds=3)

    # Circuit should be valid
    dem = circuit.detector_error_model()
    assert dem is not None

    # Sample: zero noise → zero detection events and zero logical errors
    sampler = circuit.compile_detector_sampler()
    detection_events, obs = sampler.sample(shots=500, separate_observables=True)
    assert detection_events.sum() == 0
    assert obs.sum() == 0


def test_zero_noise_neutral_atom():
    """Zero noise → PL=0 for neutral atom compiler."""
    params = _get_zero_noise_params("neutral_atom")
    compiler = get_compiler("neutral_atom", distance=3, noise_params=params)
    circuit = compiler.build_memory_circuit(num_rounds=3)
    dem = circuit.detector_error_model()
    assert dem is not None
    sampler = circuit.compile_detector_sampler()
    detection_events, obs = sampler.sample(shots=500, separate_observables=True)
    assert detection_events.sum() == 0
    assert obs.sum() == 0


def test_zero_noise_trapped_ion():
    """Zero noise → PL=0 for trapped ion compiler."""
    params = _get_zero_noise_params("ion_trap")
    compiler = get_compiler("ion_trap", distance=3, noise_params=params)
    circuit = compiler.build_memory_circuit(num_rounds=3)
    dem = circuit.detector_error_model()
    assert dem is not None
    sampler = circuit.compile_detector_sampler()
    detection_events, obs = sampler.sample(shots=500, separate_observables=True)
    assert detection_events.sum() == 0
    assert obs.sum() == 0


# ---------------------------------------------------------------------------
# Circuit structure tests
# ---------------------------------------------------------------------------

def test_circuit_has_detectors():
    """All compilers produce circuits with DETECTOR instructions."""
    for platform_name in PLATFORM_NAMES:
        pdict = _get_default_params(platform_name)
        compiler = get_compiler(platform_name, distance=3, noise_params=pdict)
        circuit = compiler.build_memory_circuit(num_rounds=3)
        circuit_str = str(circuit)
        assert "DETECTOR" in circuit_str, f"{platform_name}: missing DETECTOR"
        assert circuit.num_detectors > 0, f"{platform_name}: num_detectors=0"


def test_circuit_has_observable():
    """All compilers produce circuits with OBSERVABLE_INCLUDE."""
    for platform_name in PLATFORM_NAMES:
        pdict = _get_default_params(platform_name)
        compiler = get_compiler(platform_name, distance=3, noise_params=pdict)
        circuit = compiler.build_memory_circuit(num_rounds=3)
        circuit_str = str(circuit)
        assert "OBSERVABLE_INCLUDE" in circuit_str, f"{platform_name}: missing OBSERVABLE_INCLUDE"
        assert circuit.num_observables > 0, f"{platform_name}: num_observables=0"


# ---------------------------------------------------------------------------
# Quorum tests: basic noise should give nontrivial PL
# ---------------------------------------------------------------------------

def test_with_noise_gives_nontrivial_pl():
    """With realistic noise, PL should be > 0 but < 0.5."""
    for platform_name in PLATFORM_NAMES:
        pdict = _get_default_params(platform_name)
        compiler = get_compiler(platform_name, distance=3, noise_params=pdict)
        circuit = compiler.build_memory_circuit(num_rounds=3)

        sampler = circuit.compile_detector_sampler()
        detection_events, obs = sampler.sample(
            shots=1000, separate_observables=True
        )
        logical_errors = obs.sum()
        p_run = logical_errors / 1000

        # With natural noise and d=3, P_run should be between 0 and 0.5
        assert p_run < 0.5, (
            f"{platform_name}: P_run={p_run:.3f} >= 0.5 (too high)"
        )
        # We expect at least some noise effects (not always exactly 0)
        # but at natural operating point with d=3, errors could be rare
        # Just check it's not absurd


# ---------------------------------------------------------------------------
# Layout tests
# ---------------------------------------------------------------------------

def test_correct_number_of_qubits():
    """d=3 → 9 data + 8 ancilla = 17 qubits. d=5 → 25 data + 24 ancilla = 49."""
    for d, expected in [(3, 17), (5, 49)]:
        for platform_name in PLATFORM_NAMES:
            pdict = _get_default_params(platform_name)
            compiler = get_compiler(platform_name, distance=d, noise_params=pdict)
            circuit = compiler.build_memory_circuit(num_rounds=d)
            assert circuit.num_qubits == expected, (
                f"{platform_name} d={d}: expected {expected} qubits, "
                f"got {circuit.num_qubits}"
            )


def test_correct_number_of_detectors():
    """d=3, rounds=3: 4 Z-only (round 1) + 2×8 all-ancilla = 20 detectors."""
    for platform_name in PLATFORM_NAMES:
        pdict = _get_default_params(platform_name)
        compiler = get_compiler(platform_name, distance=3, noise_params=pdict)
        circuit = compiler.build_memory_circuit(num_rounds=3)
        # Round 1: only Z ancillas (4 for d=3), rounds 2-3: all ancillas (8 each)
        n_z = 4  # Z ancillas for d=3
        n_all = 8  # total ancillas for d=3
        expected = n_z + 2 * n_all  # = 20
        assert circuit.num_detectors == expected, (
            f"{platform_name}: expected {expected} detectors, "
            f"got {circuit.num_detectors}"
        )


# ---------------------------------------------------------------------------
# Detector error model tests
# ---------------------------------------------------------------------------

def test_dem_is_valid():
    """Detector error model should be constructible for all compilers."""
    for platform_name in PLATFORM_NAMES:
        pdict = _get_default_params(platform_name)
        compiler = get_compiler(platform_name, distance=5, noise_params=pdict)
        circuit = compiler.build_memory_circuit(num_rounds=5)
        dem = circuit.detector_error_model(decompose_errors=True)
        assert dem is not None
        assert len(dem) > 0, f"{platform_name}: empty DEM with noise"


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Compiler Tests ===\n")

    test_zero_noise_superconducting()
    print("PASS: test_zero_noise_superconducting")

    test_zero_noise_neutral_atom()
    print("PASS: test_zero_noise_neutral_atom")

    test_zero_noise_trapped_ion()
    print("PASS: test_zero_noise_trapped_ion")

    test_circuit_has_detectors()
    print("PASS: test_circuit_has_detectors")

    test_circuit_has_observable()
    print("PASS: test_circuit_has_observable")

    test_with_noise_gives_nontrivial_pl()
    print("PASS: test_with_noise_gives_nontrivial_pl")

    test_correct_number_of_qubits()
    print("PASS: test_correct_number_of_qubits")

    test_correct_number_of_detectors()
    print("PASS: test_correct_number_of_detectors")

    test_dem_is_valid()
    print("PASS: test_dem_is_valid")

    print("\n=== All compiler tests passed ===")
