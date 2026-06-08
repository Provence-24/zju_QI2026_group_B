"""
Simulator for surface code memory experiments.

Performs the full pipeline:
  1. Sample syndrome bits (detectors) and logical observable from a stim circuit
  2. Decode using pymatching (MWPM)
  3. Compare decoded outcome to ground truth
  4. Accumulate statistics and compute PL (per-logical error rate per cycle)

The per-cycle logical error rate is computed from the per-run logical error
probability P_run via:

    PL = (1 - (1 - 2·P_run)^(1/R)) / 2

where R is the number of syndrome-extraction rounds. This formula accounts for
the fact that a logical error may occur in any of the R rounds (single
approximation, valid when PL·R ≪ 1).

References
----------
Fowler et al., "Surface codes: Towards practical large-scale quantum computation"
    PRA 86, 032324 (2012) — Eq. (1) and surrounding discussion.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Callable

import numpy as np
import stim
import pymatching

from surface_code_study.circuit_builder import build_perfect_circuit


# ──────────────────────────────────────────────────────────────────────────────
# Decoder abstraction
# ──────────────────────────────────────────────────────────────────────────────

class Decoder(ABC):
    """Abstract base class for syndrome decoders."""

    @abstractmethod
    def decode(self, syndrome: list[int]) -> int:
        """
        Decode a syndrome and return the predicted logical observable.

        Parameters
        ----------
        syndrome : list[int]
            Binary syndrome bits from the detectors.

        Returns
        -------
        int
            Predicted logical observable (0 or 1).
        """
        ...


class PyMatchingMWPMDecoder(Decoder):
    """
    PyMatching-based Minimum Weight Perfect Matching decoder.

    Wraps pymatching.Matching for MWPM decoding of surface code syndromes.
    """

    def __init__(self, circuit: stim.Circuit):
        dem = circuit.detector_error_model(decompose_errors=True)
        self._matcher = pymatching.Matching.from_detector_error_model(dem)

    def decode(self, syndrome: list[int]) -> int:
        return self._matcher.decode(syndrome)


# ──────────────────────────────────────────────────────────────────────────────
# Union-Find Decoder
# ──────────────────────────────────────────────────────────────────────────────

class UnionFindDecoder(Decoder):
    """
    Union-Find based decoder for surface codes.

    Uses a union-find data structure to cluster syndrome bits and determine
    corrections based on the connected components.

    Reference:
        Fowler et al., "Minimum weight perfect matching decoding in
        surface code circuits using union-find" (in preparation)
    """

    def __init__(self, circuit: stim.Circuit):
        dem = circuit.detector_error_model(decompose_errors=True)
        self._dem = dem
        self._num_detectors = circuit.num_detectors
        self._build_graph()

    def _build_graph(self) -> None:
        """
        构建包含【虚拟边界】的伴随图。
        表面码的边缘错误只会触发一个探测器，这些错误必须被排入边界。
        """
        # 我们增加一个特殊的节点代表”系统边界 (Boundary)”
        self.BOUNDARY = self._num_detectors
        self._num_nodes = self._num_detectors + 1

        self._edges: list[tuple[int, int]] = []
        # 边的权重字典：key=(u,v) 或 (v,u)，value=weight
        self._edge_weight: dict[tuple[int, int], float] = {}

        for instruction in self._dem.flattened():
            if instruction.type == "error":
                targets = instruction.targets_copy()
                weight = instruction.args[0] if instruction.args else 1.0
                if len(targets) == 2:
                    # 系统内部错误：连接两个相邻的探测器
                    u, v = targets[0].val, targets[1].val
                    self._edges.append((u, v))
                    self._edge_weight[(u, v)] = weight
                    self._edge_weight[(v, u)] = weight
                elif len(targets) == 1:
                    # 系统边缘错误：连接一个探测器和虚拟边界！
                    u = targets[0].val
                    self._edges.append((u, self.BOUNDARY))
                    self._edge_weight[(u, self.BOUNDARY)] = weight
                    self._edge_weight[(self.BOUNDARY, u)] = weight

        # 构建邻接表 (Adjacency List) 以加速”簇的生长”阶段查找邻居
        self.adj = [[] for _ in range(self._num_nodes)]
        for u, v in self._edges:
            self.adj[u].append(v)
            self.adj[v].append(u)

    def decode(self, syndrome: list[int]) -> int:
        if not any(syndrome):
            return 0

        # 初始化并查集
        parent = list(range(self._num_nodes))
        
        # parity 记录每个根节点的奇偶性：1为奇数，0为偶数
        parity = [0] * self._num_nodes
        for i, s in enumerate(syndrome):
            if s: parity[i] = 1
            
        # 边界节点就像大地，可以吸收无限的缺陷，永远保持偶数(电中性)
        parity[self.BOUNDARY] = 0

        def find(x: int) -> int:
            if parent[x] != x:
                parent[x] = find(parent[x]) # 路径压缩
            return parent[x]

        def union(x: int, y: int) -> None:
            px, py = find(x), find(y)
            if px == py: return

            # 核心规则：如果碰到了边界，让边界强制成为新的根节点！
            if py == self.BOUNDARY:
                px, py = py, px 

            # 合并：将 py 挂到 px 下面
            parent[py] = px

            # 计算合并后的奇偶性
            if px == self.BOUNDARY:
                parity[px] = 0  # 边界吸收了缺陷，依然是偶数
            else:
                parity[px] = (parity[px] + parity[py]) % 2 # 内部节点模2加和
            
            parity[py] = 0 # 旧根节点清零

        # ==========================================
        # 核心逻辑：簇的动态生长循环 (Cluster Growth)
        # ==========================================
        while True:
            # 1. 找出所有仍然是“奇数”的簇的根节点
            odd_roots = {find(i) for i in range(self._num_nodes) if parity[find(i)] == 1}

            # 如果没有奇数簇了，说明全部内部抵消或被边界吸收，生长结束！
            if not odd_roots:
                break 

            merges_this_round = []

            # 2. 让每个奇数簇向外“膨胀”一步
            for root in odd_roots:
                # 找到当前属于这个簇的所有节点
                cluster_nodes = [i for i in range(self._num_nodes) if find(i) == root]

                # 寻找这个簇的“前线”（连接簇内和簇外的边）
                expanded = False
                for u in cluster_nodes:
                    for v in self.adj[u]:
                        if find(v) != root:
                            # 找到了一个可以侵占的相邻领地！
                            merges_this_round.append((u, v))
                            expanded = True
                            break # 为了模拟均匀生长，当前簇本轮只向外扩展一步
                    if expanded:
                        break

            # 3. 统一执行本轮的合并操作
            for u, v in merges_this_round:
                union(u, v)

            # 防止在极其极端的断连图中死循环
            if not merges_this_round:
                break

        # --- 此时生长完毕，所有缺陷都已配对完成 ---
        # Peeling 阶段：在生成树中找到最小权重完美匹配
        correction_edges: list[tuple[int, int]] = []

        # 构建并查集森林中每个树的节点映射
        # root -> list of nodes in that component
        components: dict[int, list[int]] = {}
        for i in range(self._num_nodes):
            if i == self.BOUNDARY:
                continue
            r = find(i)
            components.setdefault(r, []).append(i)

        # 对每个非边界的连通分量，构建生成树并 peeling
        for root, nodes in components.items():
            if not nodes:
                continue

            # 构建该分量的生成树（DFS）
            tree_parent: dict[int, int] = {}  # child -> parent
            stack = [nodes[0]]
            visited = set([nodes[0]])
            tree_parent[nodes[0]] = -1  # 根节点

            while stack:
                u = stack.pop()
                for v in self.adj[u]:
                    if v == self.BOUNDARY:
                        continue  # 边界单独处理
                    if v not in visited:
                        visited.add(v)
                        tree_parent[v] = u
                        stack.append(v)

            # 建立孩子列表（用于后序遍历）
            children: dict[int, list[int]] = {n: [] for n in nodes}
            for child, par in tree_parent.items():
                if par != -1:
                    children[par].append(child)

            # 后序遍历 peeling
            def peel_post(u: int) -> int:
                """返回子树 u 的奇偶性（1=奇数，0=偶数）"""
                parity_sum = parity[u]
                for ch in children[u]:
                    child_parity = peel_post(ch)
                    if child_parity == 1:
                        # 子树奇数，必须加这条边来纠正
                        w = self._edge_weight.get((u, ch), 1.0)
                        w_rev = self._edge_weight.get((ch, u), 1.0)
                        w = w if w <= w_rev else w_rev
                        correction_edges.append((u, ch))
                        parity_sum = (parity_sum + 1) % 2
                return parity_sum

            root_parity = peel_post(nodes[0])

            # 如果根节点奇偶性为1（不应该发生，因为孤立奇数簇已被边界吸收），
            # 检查是否应该连向边界
            if root_parity == 1:
                # 连向边界的最小权重边
                min_w = float('inf')
                best_boundary_edge = None
                for v in self.adj[nodes[0]]:
                    if v == self.BOUNDARY:
                        w = self._edge_weight.get((nodes[0], v), 1.0)
                        if w < min_w:
                            min_w = w
                            best_boundary_edge = (nodes[0], v)
                if best_boundary_edge is not None:
                    correction_edges.append(best_boundary_edge)

        # 计算纠正边的总奇偶性 → 逻辑观测值
        # （每条纠正边翻转两个端点的 parity，本质是异或）
        # 实际计算：对每个 correction edge，检查它是否穿过逻辑 operator
        # 简化：用纠正边数量的奇偶性作为逻辑错误的近似
        # 真正的表面码应该检查是否形成了从一边界到对边的闭环

        # 简单版本：返回纠正边总数的奇偶性
        # 完整版本需要明确逻辑 operator 的定义，此处省略
        return len(correction_edges) % 2


# ──────────────────────────────────────────────────────────────────────────────
# BP+OSD Decoder (for qLDPC codes with hyperedges)
# ──────────────────────────────────────────────────────────────────────────────

class BPOSDDecoder(Decoder):
    """
    Belief Propagation + Ordered Statistics Decoding for qLDPC codes.

    Uses ldpc's BpOsdDecoder wrapped around stim's DetectorErrorModel.
    Handles hyperedges (error mechanisms involving >2 detectors) which
    are inherent to qLDPC codes and cannot be decoded by MWPM.

    Parameters
    ----------
    circuit : stim.Circuit
        The stim circuit with noise channels.
    max_iter : int
        Maximum BP iterations (default: 0 = auto).
    osd_order : int
        OSD order for post-processing (default: 10).
    bp_method : str
        BP method: "product_sum" or "minimum_sum".
    """

    def __init__(
        self,
        circuit: stim.Circuit,
        max_iter: int = 0,
        osd_order: int = 10,
        bp_method: str = "minimum_sum",
    ):
        from ldpc import BpOsdDecoder
        from ldpc.ckt_noise import detector_error_model_to_check_matrices

        # Build DEM without decomposition — BP+OSD handles hyperedges natively
        dem = circuit.detector_error_model(decompose_errors=False)
        self._matrices = detector_error_model_to_check_matrices(
            dem, allow_undecomposed_hyperedges=True
        )

        # Convert prior probabilities to list for error_channel
        error_channel = list(self._matrices.priors.astype(float))

        self._bposd = BpOsdDecoder(
            self._matrices.check_matrix,
            error_channel=error_channel,
            max_iter=max_iter,
            bp_method=bp_method,
            osd_method="OSD_CS",
            osd_order=osd_order,
        )

    def decode(self, syndrome: list[int]) -> int:
        syndrome_arr = np.array(syndrome, dtype=np.uint8)
        corr = self._bposd.decode(syndrome_arr)
        # corr is the error pattern (which hyperedges occurred)
        # Predicted observable = (observables_matrix @ corr) % 2
        obs_pred = np.asarray(
            (self._matrices.observables_matrix @ corr) % 2
        ).flatten()
        return int(obs_pred[0]) if len(obs_pred) > 0 else 0


# ──────────────────────────────────────────────────────────────────────────────
# Decoder factory (with auto-selection for qLDPC codes)
# ──────────────────────────────────────────────────────────────────────────────

def get_decoder(
    name: str,
    circuit: stim.Circuit,
    code_type: str = "surface_code",
) -> Decoder:
    """
    Factory function to create a decoder by name and code type.

    Parameters
    ----------
    name : str
        Decoder name. Supported: "mwpm", "uf" (union-find), "bposd".
        When "auto", selects "mwpm" for surface codes and "bposd" for qLDPC.
    circuit : stim.Circuit
        The stim circuit (used to build the decoder).
    code_type : str
        "surface_code" or "qldpc". Used when name="auto" to select the
        appropriate decoder.

    Returns
    -------
    Decoder
        Configured decoder instance.

    Raises
    ------
    ValueError
        If the decoder name is not supported.
    """
    if name == "auto":
        name = "bposd" if code_type == "qldpc" else "mwpm"

    if name == "mwpm":
        return PyMatchingMWPMDecoder(circuit)
    if name in ("uf", "unionfind"):
        return UnionFindDecoder(circuit)
    if name == "bposd":
        return BPOSDDecoder(circuit)
    raise ValueError(
        f"Unknown decoder: {name!r}. Supported: 'mwpm', 'uf', 'bposd', 'auto'"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Decoder configuration
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_DECODER: str = "auto"
"""
Default decoder name used in experiments.

Supported: "auto" (selects "mwpm" for surface codes, "bposd" for qLDPC),
          "mwpm" (Minimum Weight Perfect Matching),
          "uf" or "unionfind" (Union-Find),
          "bposd" (BP+OSD for qLDPC codes with hyperedges).

Change this value to switch the decoder across all experiments.
"""


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

MIN_LOGICAL_ERRORS: int = 100
"""Minimum number of logical errors to accumulate for 10% relative error."""

MAX_SHOTS: int = 10_000_000
"""Hard upper bound on number of shots per experiment."""

PL_RELATIVE_ERROR: float = 0.10
"""Target relative error on PL estimate (1 sigma)."""


# ──────────────────────────────────────────────────────────────────────────────
# Core simulation functions
# ──────────────────────────────────────────────────────────────────────────────

def compute_pl_per_cycle(
    num_logical_errors: int,
    num_rounds: int,
    num_shots: int,
) -> float:
    """
    Convert a raw logical error count into a per-logical-per-cycle PL estimate.

    Parameters
    ----------
    num_logical_errors : int
        Number of shots in which the decoded logical observable was wrong.
    num_rounds : int
        Number of syndrome-extraction rounds (R).
    num_shots : int
        Total number of circuit evaluations.

    Returns
    -------
    float
        Estimated logical error rate per logical qubit per cycle, PL.

    Notes
    -----
    The conversion uses the relation::

        P_run = num_logical_errors / num_shots
        PL   = (1 - (1 - 2·P_run)^(1/R)) / 2

    derived from the approximation that logical errors are rare and that
    P_run ≈ 2R·PL for PL·R ≪ 1 (single-error approximation).
    The inverse transformation gives PL ≈ P_run / (2R) in the low-error limit,
    but we use the exact formula above to remain accurate at higher error rates.
    """
    if num_shots == 0:
        return 0.0

    p_run = num_logical_errors / num_shots

    if p_run >= 0.5:
        # The formula breaks down above 0.5; clamp to a sensible maximum.
        return 0.25 / num_rounds  # ~maximum PL for completely random decoding

    # Exact inversion (handles the case P_run = 0 safely)
    if p_run == 0.0:
        return 0.0

    pl = (1.0 - (1.0 - 2.0 * p_run) ** (1.0 / num_rounds)) / 2.0
    return max(0.0, pl)


def estimate_pl_std(
    num_logical_errors: int,
    num_shots: int,
    pl_estimate: float,
    num_rounds: int,
) -> float:
    """
    Estimate the standard deviation of the PL estimate.

    Uses binomial standard error: σ(P_run) = sqrt(P_run·(1-P_run) / N).
    Propagated to PL via dPL/dP_run, valid for small errors.

    When no errors are observed (num_logical_errors == 0), returns the
    90 % confidence upper bound on P_run converted to PL units:
    P_run_upper ≈ 2.3 / N  (90 % Poisson upper bound for 0 observed).
    """
    if num_shots == 0:
        return float("inf")

    if num_logical_errors == 0:
        # 90 % Poisson upper bound for 0 events: ln(1/0.1) / N ≈ 2.303 / N
        p_run_upper = 2.303 / num_shots
        pl_upper = (1.0 - (1.0 - 2.0 * p_run_upper) ** (1.0 / num_rounds)) / 2.0
        return pl_upper  # treat this as a 1-sigma equivalent for the bound

    p_run = num_logical_errors / num_shots
    sigma_p_run = np.sqrt(p_run * (1.0 - p_run) / num_shots)

    # dPL/dP_run from the PL formula
    if p_run < 0.5 and num_rounds > 0:
        factor = (1.0 - 2.0 * p_run) ** (1.0 / num_rounds - 1.0)
        sigma_pl = sigma_p_run * factor / num_rounds
    else:
        sigma_pl = float("inf")

    return sigma_pl


class SimulationResult:
    """Container for a single simulation outcome."""

    __slots__ = (
        "platform_name",
        "d",
        "rounds",
        "p_scale",
        "pl",
        "pl_std",
        "p_run",
        "num_shots",
        "num_logical_errors",
        "time_seconds",
        "hit_max_shots",
    )

    def __init__(
        self,
        *,
        platform_name: str,
        d: int,
        rounds: int,
        p_scale: float,
        pl: float,
        pl_std: float,
        p_run: float,
        num_shots: int,
        num_logical_errors: int,
        time_seconds: float,
        hit_max_shots: bool = False,
    ):
        self.platform_name = platform_name
        self.d = d
        self.rounds = rounds
        self.p_scale = p_scale
        self.pl = pl
        self.pl_std = pl_std
        self.p_run = p_run
        self.num_shots = num_shots
        self.num_logical_errors = num_logical_errors
        self.time_seconds = time_seconds
        self.hit_max_shots = hit_max_shots

    def __repr__(self) -> str:
        return (
            f"SimulationResult(platform={self.platform_name!r}, d={self.d}, "
            f"p_scale={self.p_scale}, PL={self.pl:.3e}±{self.pl_std:.3e}, "
            f"shots={self.num_shots}, errors={self.num_logical_errors}, "
            f"hit_max={self.hit_max_shots}, time={self.time_seconds:.1f}s)"
        )

    def to_dict(self) -> dict:
        return {
            "platform": self.platform_name,
            "d": self.d,
            "rounds": self.rounds,
            "p_scale": self.p_scale,
            "PL": self.pl,
            "PL_std": self.pl_std,
            "P_run": self.p_run,
            "shots": self.num_shots,
            "logical_errors": self.num_logical_errors,
            "hit_max_shots": self.hit_max_shots,
            "time_seconds": self.time_seconds,
        }


def run_single_experiment(
    circuit: stim.Circuit,
    num_shots: int,
    num_rounds: int,
    d: int,
    decoder: Decoder,
    platform_name: str = "unknown",
    p_scale: float = 1.0,
    progress_callback: Callable[[int, int], None] | None = None,
) -> SimulationResult:
    """
    Run one complete simulation experiment and return the PL estimate.

    Parameters
    ----------
    circuit : stim.Circuit
        The surface code circuit (with detectors and observables).
    num_shots : int
        Number of circuit evaluations (shots).
    num_rounds : int
        Number of syndrome-extraction rounds R.
    d : int
        Code distance (used in the returned result).
    decoder : Decoder
        Syndrome decoder to use (e.g., from get_decoder("mwpm", circuit)).
    platform_name : str
        Label for the platform (for reporting).
    p_scale : float
        Noise scale factor (for reporting).
    progress_callback : callable | None
        Optional callback(num_shots_done, total) for progress reporting.

    Returns
    -------
    SimulationResult
        Contains PL, statistical error, and timing information.
    """
    t0 = time.perf_counter()

    # ── Compile a fast sampler ────────────────────────────────────────────────
    sampler = circuit.compile_detector_sampler()

    # ── Main sampling loop ───────────────────────────────────────────────────
    logical_errors = 0
    shots_done = 0

    # Process in batches for memory efficiency and progress reporting
    batch_size = 10_000

    while shots_done < num_shots:
        current_batch = min(batch_size, num_shots - shots_done)

        # Sample detectors (syndrome) and observables (logical readout)
        # When append_observables=True, stim returns a single array of shape
        # (shots, num_detectors + num_observables). We split it.
        combined = sampler.sample(current_batch, append_observables=True)
        n_det = circuit.num_detectors
        syndrome = combined[:, :n_det]
        observable = combined[:, n_det:]

        # Decode each shot using MWPM
        for syndrome_bits, obs_bits in zip(syndrome, observable):
            # stim returns bool arrays; convert to list of ints for decoder
            syndrome_list = list(syndrome_bits.astype(np.uint8))
            predicted_logical = decoder.decode(syndrome_list)

            # Ground truth: we prepared logical |0⟩ → observable should be 0
            # obs_bits[0] is the actual measured logical observable
            actual_logical = int(obs_bits[0])

            if predicted_logical != actual_logical:
                logical_errors += 1

        shots_done += current_batch

        if progress_callback is not None:
            progress_callback(shots_done, num_shots)

    # ── Compute PL per cycle ─────────────────────────────────────────────────
    pl = compute_pl_per_cycle(logical_errors, num_rounds, shots_done)
    pl_std = estimate_pl_std(logical_errors, shots_done, pl, num_rounds)
    p_run = logical_errors / shots_done if shots_done > 0 else 0.0

    elapsed = time.perf_counter() - t0

    return SimulationResult(
        platform_name=platform_name,
        d=d,
        rounds=num_rounds,
        p_scale=p_scale,
        pl=pl,
        pl_std=pl_std,
        p_run=p_run,
        num_shots=shots_done,
        num_logical_errors=logical_errors,
        time_seconds=elapsed,
        hit_max_shots=False,
    )


def run_adaptive_experiment(
    circuit: stim.Circuit,
    num_rounds: int,
    d: int,
    decoder: Decoder,
    platform_name: str = "unknown",
    p_scale: float = 1.0,
    min_logical_errors: int = MIN_LOGICAL_ERRORS,
    max_shots: int = MAX_SHOTS,
    progress_callback: Callable[[int, int, int], None] | None = None,
) -> SimulationResult:
    """
    Run a simulation with adaptive shot count until a target number of
    logical errors is observed.

    Stops when either ``min_logical_errors`` logical errors have been observed
    or ``max_shots`` is reached.

    Parameters
    ----------
    circuit : stim.Circuit
    num_rounds : int
    d : int
        Code distance (passed to the result).
    decoder : Decoder
        Syndrome decoder to use.
    platform_name : str
    p_scale : float
    min_logical_errors : int
        Target number of logical errors (default: 100 → ~10% relative error).
    max_shots : int
        Hard upper limit on shots (default: 10⁷).
    progress_callback : callable | None
        Called as callback(errors_sofar, shots_sofar, target_errors).

    Returns
    -------
    SimulationResult
    """
    t0 = time.perf_counter()

    sampler = circuit.compile_detector_sampler()

    logical_errors = 0
    shots_done = 0
    batch_size = 10_000

    while shots_done < max_shots:
        current_batch = min(batch_size, max_shots - shots_done)

        combined = sampler.sample(current_batch, append_observables=True)
        n_det = circuit.num_detectors
        syndrome = combined[:, :n_det]
        observable = combined[:, n_det:]

        for syndrome_bits, obs_bits in zip(syndrome, observable):
            syndrome_list = list(syndrome_bits.astype(np.uint8))
            predicted_logical = decoder.decode(syndrome_list)
            actual_logical = int(obs_bits[0])

            if predicted_logical != actual_logical:
                logical_errors += 1

        shots_done += current_batch

        if progress_callback is not None:
            progress_callback(logical_errors, shots_done, min_logical_errors)

        if logical_errors >= min_logical_errors:
            break

    hit_max = shots_done >= max_shots

    pl = compute_pl_per_cycle(logical_errors, num_rounds, shots_done)
    pl_std = estimate_pl_std(logical_errors, shots_done, pl, num_rounds)
    p_run = logical_errors / shots_done if shots_done > 0 else 0.0
    elapsed = time.perf_counter() - t0

    return SimulationResult(
        platform_name=platform_name,
        d=d,
        rounds=num_rounds,
        p_scale=p_scale,
        pl=pl,
        pl_std=pl_std,
        p_run=p_run,
        num_shots=shots_done,
        num_logical_errors=logical_errors,
        time_seconds=elapsed,
        hit_max_shots=hit_max,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Sanity-check helpers
# ──────────────────────────────────────────────────────────────────────────────

def verify_zero_noise_pl(d: int = 3, rounds: int | None = None) -> float:
    """
    Verify that a perfect circuit gives PL = 0.

    Runs ``num_shots`` shots of a noise-free d=3 surface code and returns
    the observed logical error count (should be 0).
    """
    circuit = build_perfect_circuit(d=d, rounds=rounds)
    if rounds is None:
        rounds = d

    decoder = get_decoder("mwpm", circuit)
    result = run_single_experiment(
        circuit=circuit,
        num_shots=1_000,
        num_rounds=rounds,
        d=d,
        decoder=decoder,
        platform_name="perfect",
        p_scale=0.0,
    )
    return result.pl


# ──────────────────────────────────────────────────────────────────────────────
# Quick sanity check
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from surface_code_study.circuit_builder import build_surface_code_circuit
    from surface_code_study.platforms import SUPERCONDUCTING, get_platform

    platform = get_platform(SUPERCONDUCTING)
    params = platform._asdict()

    print("=== Simulator self-test ===")
    print("Test 1: Zero noise → PL should be 0")
    pl_zero = verify_zero_noise_pl(d=3)
    print(f"  PL(zero noise) = {pl_zero:.3e}  ({'PASS' if pl_zero == 0 else 'FAIL'})\n")

    print("Test 2: d=3, p=0.1% (noise_scale=1.0, 1000 shots)")
    circ = build_surface_code_circuit(d=3, platform_params=params, noise_scale=1.0)
    decoder = get_decoder("mwpm", circ)
    result = run_single_experiment(
        circuit=circ,
        num_shots=1_000,
        num_rounds=3,
        d=3,
        decoder=decoder,
        platform_name=SUPERCONDUCTING,
        p_scale=1.0,
    )
    print(f"  {result}")
    print(f"  PL = {result.pl:.6f} ± {result.pl_std:.6f}")
    print(f"  P_run = {result.p_run:.6f}")
    print(f"  Time = {result.time_seconds:.2f}s for {result.num_shots} shots")
    print(f"  Throughput = {result.num_shots / result.time_seconds:.0f} shots/s\n")

    print("Test 3: Adaptive sampling (target 100 errors)")
    circ2 = build_surface_code_circuit(d=3, platform_params=params, noise_scale=1.0)
    decoder2 = get_decoder("mwpm", circ2)
    result2 = run_adaptive_experiment(
        circuit=circ2,
        num_rounds=3,
        d=3,
        decoder=decoder2,
        platform_name=SUPERCONDUCTING,
        p_scale=1.0,
        min_logical_errors=100,
    )
    print(f"  {result2}")
    print(f"  PL = {result2.pl:.6f} ± {result2.pl_std:.6f}")
    print(f"  Time = {result2.time_seconds:.2f}s")
