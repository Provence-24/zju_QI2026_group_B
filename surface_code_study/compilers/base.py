"""
Abstract base class for platform-aware surface code circuit compilers.

Each platform subclass implements build_round() to describe a complete
syndrome-extraction round with platform-specific physical operations
(movement, transport, idle decoherence, etc.).
"""

from abc import ABC, abstractmethod
import math
import stim


class PlatformCompiler(ABC):
    """
    Compiles an abstract surface code patch into a platform-specific stim.Circuit.

    Subclasses must implement _init_layout() and build_round().
    """

    def __init__(self, distance: int, noise_params: dict):
        """
        Args:
            distance: surface code code distance d. d² data qubits, d²-1 ancillas.
            noise_params: platform noise dictionary with at least:
                p_2q, p_1q, p_meas, p_reset, t_cycle_ns, T1_us, T2_us
        """
        self.d = distance
        self.params = noise_params
        self._layout = self._init_layout()

    # ------------------------------------------------------------------
    # Subclass interface
    # ------------------------------------------------------------------

    @abstractmethod
    def _init_layout(self) -> dict:
        """
        Define qubit layout.

        Returns a dict with keys:
          - 'data': List[int]          data qubit stim indices
          - 'ancilla_x': List[int]     X-type ancilla indices
          - 'ancilla_z': List[int]     Z-type ancilla indices
          - 'data_coords': dict        {qubit_index: (row, col)}
          - 'connectivity': dict       {ancilla_index: [data_qubit_indices]}
        """
        ...

    @abstractmethod
    def build_round(self, is_first_round: bool = False) -> stim.Circuit:
        """
        Build one complete syndrome-extraction round.

        Must include:
        1. ancilla init (R + reset noise)
        2. Hadamards on X ancillas
        3. Platform-specific two-qubit gate sequence (with idle noise)
        4. TICK markers
        5. ancilla measurement (with measurement noise)
        6. DETECTOR markers
        """
        ...

    # ------------------------------------------------------------------
    # Shared layout builder (rotated surface code)
    # ------------------------------------------------------------------

    def _build_rotated_layout(self) -> dict:
        """
        Build the standard rotated surface code layout.

        Data qubits at (odd, odd) coordinates: (2r+1, 2c+1) for r,c in [0,d-1].
        Ancillas at a subset of (even, even) coordinates in [0, 2d]×[0, 2d].

        Checkerboard pattern:
          - Bulk (4 data neighbours): all (d-1)² positions are ancillas.
            X if (r'+c') odd, Z if (r'+c') even, where r'=row/2, c'=col/2.
          - Boundary (2 data neighbours): alternating subset.
            Left/Right boundaries: X type.  Top/Bottom boundaries: Z type.
          - Corner positions (< 2 neighbours): no ancilla.

        Total: d² data + d²-1 ancilla = 2d²-1 qubits, contiguously indexed.
        """
        d = self.d
        n_data = d * d
        max_coord = 2 * d

        # --- data qubits ---------------------------------------------------
        data = list(range(n_data))
        data_coords = {}
        _data_by_coord = {}
        idx = 0
        for r in range(d):
            for c in range(d):
                coord = (2 * r + 1, 2 * c + 1)
                data_coords[idx] = coord
                _data_by_coord[coord] = idx
                idx += 1

        # --- ancilla qubits -------------------------------------------------
        ancilla_x = []
        ancilla_z = []
        ancilla_coords = {}
        connectivity = {}
        anc_idx = n_data

        # Iterate all (even, even) positions
        for er in range(0, max_coord + 1, 2):
            for ec in range(0, max_coord + 1, 2):
                # Find neighbouring data qubits (at the 4 diagonal positions)
                nb_coords = [
                    (er - 1, ec - 1), (er - 1, ec + 1),
                    (er + 1, ec - 1), (er + 1, ec + 1),
                ]
                nb = []
                for nc in nb_coords:
                    if nc in _data_by_coord:
                        nb.append(_data_by_coord[nc])

                if len(nb) < 2:
                    continue  # corner — no ancilla

                rp = er // 2  # "data-grid" row index (0 .. d)
                cp = ec // 2  # "data-grid" col index (0 .. d)

                is_bulk = (len(nb) == 4)

                # Determine if this position hosts an ancilla
                if is_bulk:
                    include = True
                elif er == 0:
                    # Top boundary
                    include = (cp % 2 == 0)
                elif ec == 0:
                    # Left boundary
                    include = (rp % 2 == 1)
                elif er == max_coord:
                    # Bottom boundary
                    include = ((d + cp) % 2 == 0)
                elif ec == max_coord:
                    # Right boundary
                    include = ((rp + d) % 2 == 1)
                else:
                    include = False  # should not happen

                if not include:
                    continue

                ancilla_coords[anc_idx] = (er, ec)
                connectivity[anc_idx] = nb

                # X vs Z type
                is_x = False
                if is_bulk:
                    is_x = ((rp + cp) % 2 == 1)
                elif er == 0:
                    is_x = False  # Top → Z
                elif ec == 0:
                    is_x = True   # Left → X
                elif er == max_coord:
                    is_x = False  # Bottom → Z
                elif ec == max_coord:
                    is_x = True   # Right → X

                if is_x:
                    ancilla_x.append(anc_idx)
                else:
                    ancilla_z.append(anc_idx)

                anc_idx += 1

        ancillas = list(range(n_data, anc_idx))

        return {
            'data': data,
            'ancilla_x': ancilla_x,
            'ancilla_z': ancilla_z,
            'ancillas': ancillas,
            'ancilla_coords': ancilla_coords,
            'data_coords': data_coords,
            'connectivity': connectivity,
        }

    # ------------------------------------------------------------------
    # Shared circuit building
    # ------------------------------------------------------------------

    def build_memory_circuit(self, num_rounds: int) -> stim.Circuit:
        """
        Build full memory experiment circuit.

        Structure: qubit coords → data init → (num_rounds) × build_round()
        → final data measurement → logical observable.
        """
        circuit = stim.Circuit()

        # Qubit coordinates for stim visualization and PyMatching
        all_coords = dict(self._layout['data_coords'])
        if 'ancilla_coords' in self._layout:
            all_coords.update(self._layout['ancilla_coords'])
        else:
            for q, (r, c) in self._layout['data_coords'].items():
                pass

        for qidx in sorted(all_coords.keys()):
            r, c = all_coords[qidx]
            circuit.append("QUBIT_COORDS", [qidx], [float(r), float(c)])

        # Initialize all data qubits in |0⟩
        data = self._layout['data']
        circuit.append("R", data)
        circuit.append("X_ERROR", data, self.params['p_reset'])

        # Syndrome extraction rounds
        for i in range(num_rounds):
            circuit += self.build_round(is_first_round=(i == 0))

        # Final data qubit measurement
        circuit.append("M", data)

        # Logical observable
        circuit += self._add_logical_observable()

        return circuit

    def _add_logical_observable(self) -> stim.Circuit:
        """
        Default: logical Z operator = product of leftmost column data qubits.

        Data coords are (2r+1, 2c+1), so the leftmost column has c-coordinate = 1.
        References the final data qubit measurements via rec targets.
        """
        obs_circuit = stim.Circuit()
        data = self._layout['data']
        n_data = len(data)
        # Find the minimum column coordinate among data qubits
        min_col = min(c for _, (r, c) in self._layout['data_coords'].items())
        left_col = [
            q for q, (r, c) in self._layout['data_coords'].items()
            if c == min_col
        ]
        data_pos = {q: i for i, q in enumerate(data)}
        targets = [stim.target_rec(-n_data + data_pos[q]) for q in sorted(left_col)]
        obs_circuit.append("OBSERVABLE_INCLUDE", targets, 0)
        return obs_circuit

    # ------------------------------------------------------------------
    # Noise helpers
    # ------------------------------------------------------------------

    def idle_noise(self, qubits: list[int], duration_ns: float) -> stim.Circuit:
        """
        Apply idle decoherence noise via PAULI_CHANNEL_1.

        Uses the asymmetric Pauli channel derived from T1/T2:

          p_x = 0.25 * (1 - exp(-t/T1))
          p_y = 0.25 * (1 - exp(-t/T1))
          p_z = 0.5 * (1 - exp(-t/T2)) - p_x   (clamped to ≥ 0)

        Parameters
        ----------
        qubits : list[int]
            Qubit indices to apply noise to.
        duration_ns : float
            Idle duration in nanoseconds.
        """
        T1_ns = self.params['T1_us'] * 1000.0
        T2_ns = self.params['T2_us'] * 1000.0
        T2_ns = min(T2_ns, 2.0 * T1_ns)

        if duration_ns <= 0 or T1_ns <= 0:
            return stim.Circuit()

        p_x = 0.25 * (1.0 - math.exp(-duration_ns / T1_ns))
        p_y = 0.25 * (1.0 - math.exp(-duration_ns / T1_ns))
        p_z = 0.5 * (1.0 - math.exp(-duration_ns / T2_ns)) - p_x
        p_z = max(p_z, 0.0)

        c = stim.Circuit()
        if qubits and (p_x + p_y + p_z) > 1e-12:
            c.append("PAULI_CHANNEL_1", qubits, [p_x, p_y, p_z])
        return c

    def idle_noise_except(
        self, active_qubits: list[int], duration_ns: float
    ) -> stim.Circuit:
        """Apply idle noise to all data and ancilla qubits except the active set."""
        all_qubits = list(range(len(self._layout['data']) + len(self._layout['ancillas'])))
        idle = [q for q in all_qubits if q not in active_qubits]
        return self.idle_noise(idle, duration_ns)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @property
    def all_qubits(self) -> list[int]:
        """All qubit indices (data + ancilla)."""
        return self._layout['data'] + self._layout['ancillas']
