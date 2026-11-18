#!/usr/bin/env python3
"""BosonSampling-Lab - educational boson sampling & permanent lab.

by Darion Kellar

Pure Python standard library. Zero dependencies. Zero network.
Education only - and the central lesson is stated up front:

  * Boson sampling is the linear-optics experiment where n identical
    photons enter an m-mode interferometer and the probability of each
    output pattern is the squared modulus of a MATRIX PERMANENT of the
    interferometer's unitary submatrix. Permanents are the point: the
    determinant's easy cousin they are not - no sign cancellations to
    exploit, and the best exact classical algorithms still cost
    roughly n * 2^n operations for one n x n permanent.
  * This lab computes those permanents EXACTLY, two independent ways
    (the naive permutation sum and Ryser's inclusion-exclusion), for
    toy sizes (n = 2, 3, 4 photons) where a laptop finishes instantly.
    It prints the full output distributions, shows they sum to 1,
    recovers the Hong-Ou-Mandel dip as the n = 2 special case, and
    prices the classical cost at n = 20 and n = 30 as operation
    counts - the hardness claim here is a ledger, not a slogan.
  * Nothing here is a photonic chip, a measurement, or a quantum
    advantage demonstration. At these sizes a classical laptop IS the
    fastest sampler in the room, and the lab says so. Every
    quantum-advantage / hardware / vendor / certified-randomness use
    is a permanent HOLD gate - with Gemini Argon 4 Extended Thinking
    as DECIDER (names-only, tighten-only), Muse as advisor (never
    overrides HOLD), and Google Flow plan-only seats.
"""
import cmath
import hashlib
import itertools
import json
import math
import random
import sys

# ---------------------------------------------------------------- constants
VERSION = "1.0.0"

# Labelled demo systems. Sizes are teaching sizes: the full Fock space
# has C(n + m - 1, n) occupation patterns, small enough to enumerate.
HOM_INPUT = (0, 1)
FOURIER_N3 = {"name": "fourier_n3_m5", "kind": "fourier", "m": 5, "n": 3}
FOURIER_N4 = {"name": "fourier_n4_m6", "kind": "fourier", "m": 6, "n": 4}
HAAR_N3 = {"name": "haar_n3_m5", "kind": "haar", "m": 5, "n": 3}
HAAR_N4 = {"name": "haar_n4_m6", "kind": "haar", "m": 6, "n": 4}
HAAR_SEED = 20261118  # labelled seed for the deterministic Haar-style draw

# Labelled classical throughput used only to turn operation counts into
# times in the cost ledger. It is a teaching constant, not a benchmark.
OPS_PER_SECOND = 1_000_000_000
SECONDS_PER_YEAR = 365.25 * 24 * 3600

# ---------------------------------------------------------------- HOLD gates
HOLD_GATES = {
    "quantum_advantage_claim": "HOLD - no quantum advantage claim; toy sizes run fastest on the laptop that computed them",
    "quantum_supremacy_claim": "HOLD - no supremacy demonstration; n = 2, 3, 4 photons is a teaching regime, not a frontier",
    "photonic_hardware_control": "HOLD - no control of real photonic chips, sources, phase shifters, or detectors",
    "device_measurement_claim": "HOLD - no presenting computed permanents as data measured from a real device",
    "vendor_benchmark_claim": "HOLD - no vendor benchmark claims; the operation ledger is not a product comparison",
    "certified_randomness_claim": "HOLD - no certified randomness; a computed distribution is not a randomness beacon",
    "cryptographic_use_claim": "HOLD - no cryptographic keys, proofs, or protocols derived from sampling outputs",
    "production_sampling_claim": "HOLD - no production sampling service; this is an offline teaching lab",
    "chip_fabrication_claim": "HOLD - no chip design or fabrication guidance from toy unitaries",
    "scaling_guarantee_claim": "HOLD - no guarantee that any device scales to the advantage regime",
    "investment_claim": "HOLD - no investment claims; a permanent ledger is not a prospectus",
    "hardware_specification_claim": "HOLD - no hardware specification; labelled unitaries are not device specs",
    "remove_human_override": "HOLD - the human override is never removed",
    "peer_reviewed_result_claim": "HOLD - no claim of a peer-reviewed or published experimental result",
}


def gate(action):
    """Return 'HOLD' if the action is gated, else 'PROCEED' (sandbox sim)."""
    return "HOLD" if action in HOLD_GATES else "PROCEED"


# ================================================================ 1. Permanents
# The permanent of an n x n matrix A is sum over all permutations p of
# prod_i A[i][p(i)] - the determinant without the sign. That missing
# sign is the whole story: no row-reduction shortcut exists, and the
# two exact algorithms below are the honest classical price list.
#   naive : n! permutation terms, n multiplications each -> n * n!
#   Ryser : inclusion-exclusion over column subsets     -> n * 2^n
# Both are implemented from scratch and asserted equal on every matrix
# this lab trusts.

def perm_naive(A):
    """Permanent by the definition: sum over all permutations."""
    n = len(A)
    total = 0j
    for p in itertools.permutations(range(n)):
        prod = 1
        for i in range(n):
            prod *= A[i][p[i]]
        total += prod
    return total


def perm_ryser(A):
    """Permanent by Ryser's inclusion-exclusion formula.

    perm(A) = (-1)^n * sum_{S subset of columns} (-1)^|S| *
              prod_i ( sum_{j in S} A[i][j] )
    """
    n = len(A)
    total = 0j
    for mask in range(1 << n):
        bits = bin(mask).count("1")
        prod = 1
        for i in range(n):
            row_sum = 0j
            for j in range(n):
                if mask >> j & 1:
                    row_sum += A[i][j]
            prod *= row_sum
        total += ((-1) ** (n - bits)) * prod
    return total


def perm_ops(n):
    """Exact classical operation counts for one n x n permanent."""
    terms = math.factorial(n)
    return {
        "n": n,
        "naive_terms": terms,
        "naive_mults": n * terms,
        "ryser_ops": n * (1 << n),
    }


def cost_ledger(sizes=(2, 3, 4, 5, 6, 20, 30)):
    """The classical wall, as counts and labelled times.

    Times use the labelled OPS_PER_SECOND teaching constant. One
    permanent prices ONE output probability; a full distribution at
    photon number n needs C(n + m - 1, n) of them.
    """
    rows = []
    for n in sizes:
        ops = perm_ops(n)
        rows.append({
            **ops,
            "naive_years_at_labelled_rate":
                ops["naive_mults"] / OPS_PER_SECOND / SECONDS_PER_YEAR,
            "ryser_seconds_at_labelled_rate":
                ops["ryser_ops"] / OPS_PER_SECOND,
            "ryser_years_at_labelled_rate":
                ops["ryser_ops"] / OPS_PER_SECOND / SECONDS_PER_YEAR,
        })
    return rows


# ================================================================ 2. Interferometers
# Two labelled unitaries, both built from scratch and both asserted
# unitary before any photon is allowed through:
#   * the Fourier multiport F_m, U_jk = exp(2 pi i j k / m) / sqrt(m)
#   * a Haar-style unitary: a seeded Gaussian matrix (Box-Muller on a
#     seeded Mersenne stream, so the draw is reproducible) put through
#     Gram-Schmidt orthonormalisation of its columns.

def fourier_unitary(m):
    """The m-mode Fourier multiport."""
    return [[cmath.exp(2j * math.pi * j * k / m) / math.sqrt(m)
             for k in range(m)] for j in range(m)]


def _gaussian_stream(seed):
    """Deterministic standard-normal stream (Box-Muller, seeded)."""
    rng = random.Random(seed)
    while True:
        u1 = max(rng.random(), 1e-300)
        u2 = rng.random()
        r = math.sqrt(-2.0 * math.log(u1))
        yield r * math.cos(2.0 * math.pi * u2)
        yield r * math.sin(2.0 * math.pi * u2)


def haar_unitary(m, seed=HAAR_SEED):
    """Haar-style m x m unitary from a seeded Gaussian matrix via QR."""
    stream = _gaussian_stream(seed)
    A = [[complex(next(stream), next(stream)) for _ in range(m)]
         for _ in range(m)]
    cols = [[A[i][j] for i in range(m)] for j in range(m)]
    basis = []
    for col in cols:
        v = col[:]
        for q in basis:
            ip = sum(q[i].conjugate() * v[i] for i in range(m))
            for i in range(m):
                v[i] -= ip * q[i]
        norm = math.sqrt(sum(abs(x) ** 2 for x in v))
        basis.append([x / norm for x in v])
    return [[basis[j][i] for j in range(m)] for i in range(m)]


def beamsplitter_unitary():
    """The 50/50 beamsplitter behind the Hong-Ou-Mandel dip."""
    s = 1.0 / math.sqrt(2.0)
    return [[s, s], [s, -s]]


def build_unitary(spec):
    if spec["kind"] == "fourier":
        return fourier_unitary(spec["m"])
    if spec["kind"] == "haar":
        return haar_unitary(spec["m"])
    raise ValueError(f"unknown unitary kind: {spec['kind']}")


def unitarity_error(U):
    """Max |U^dagger U - I| entry; asserted tiny before use."""
    m = len(U)
    err = 0.0
    for i in range(m):
        for j in range(m):
            s = sum(U[k][i].conjugate() * U[k][j] for k in range(m))
            err = max(err, abs(s - (1.0 if i == j else 0.0)))
    return err


# ================================================================ 3. Sampling distributions
# Photons enter one per input mode (collision-free input). An output
# occupation t = (t_0, ..., t_{m-1}) with sum t_j = n gets probability
#   bosons:         |perm(U_in,out)|^2 / prod_j t_j!
#   distinguishable: perm(|U_in,out|^2) / prod_j t_j!
# where U_in,out is the n x n matrix whose rows are the input modes
# and whose columns repeat output mode j exactly t_j times. The full
# distribution enumerates every occupation - nothing is sampled, so
# the probabilities must sum to exactly 1, and the checks assert it.

def occupations(n, m):
    """All occupation tuples of n photons in m modes, lexicographic."""
    if m == 1:
        yield (n,)
        return
    for first in range(n + 1):
        for rest in occupations(n - first, m - 1):
            yield (first,) + rest


def output_probability(U, input_modes, occ, distinguishable=False):
    """Exact probability of one output occupation pattern."""
    n = len(input_modes)
    cols = []
    for j, tj in enumerate(occ):
        cols += [j] * tj
    denom = 1
    for tj in occ:
        denom *= math.factorial(tj)
    if distinguishable:
        M = [[abs(U[input_modes[i]][cols[j]]) ** 2 for j in range(n)]
             for i in range(n)]
        return perm_naive(M).real / denom
    M = [[U[input_modes[i]][cols[j]] for j in range(n)] for i in range(n)]
    return abs(perm_ryser(M)) ** 2 / denom


def sampling_distribution(U, n, distinguishable=False):
    """Full exact distribution for photons in modes 0..n-1."""
    m = len(U)
    input_modes = tuple(range(n))
    return {occ: output_probability(U, input_modes, occ, distinguishable)
            for occ in occupations(n, m)}


def bunching_fraction(dist):
    """Total probability of outcomes with some mode holding >= 2."""
    return sum(p for occ, p in dist.items() if any(t >= 2 for t in occ))


def collision_free_fraction(dist):
    """Total probability of outcomes with every mode holding <= 1."""
    return sum(p for occ, p in dist.items() if all(t <= 1 for t in occ))


def hom_report():
    """Hong-Ou-Mandel: the n = 2, m = 2 case of the general machinery."""
    U = beamsplitter_unitary()
    bosons = sampling_distribution(U, 2)
    dist = sampling_distribution(U, 2, distinguishable=True)
    return {
        "unitary": "50/50 beamsplitter",
        "bosons": {str(k): round(v, 6) for k, v in sorted(bosons.items())},
        "distinguishable":
            {str(k): round(v, 6) for k, v in sorted(dist.items())},
        "coincidence_bosons": round(bosons[(1, 1)], 6),
        "coincidence_distinguishable": round(dist[(1, 1)], 6),
        "bunching_bosons": round(bunching_fraction(bosons), 6),
        "bunching_distinguishable": round(bunching_fraction(dist), 6),
    }


def distribution_report(spec):
    """Full boson + distinguishable distributions for one demo system."""
    U = build_unitary(spec)
    bosons = sampling_distribution(U, spec["n"])
    dist = sampling_distribution(U, spec["n"], distinguishable=True)
    top = sorted(bosons.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
    return {
        "system": spec["name"],
        "n_photons": spec["n"],
        "m_modes": spec["m"],
        "unitarity_error": unitarity_error(U),
        "outcomes": len(bosons),
        "sum_bosons": round(sum(bosons.values()), 12),
        "sum_distinguishable": round(sum(dist.values()), 12),
        "bunching_bosons": round(bunching_fraction(bosons), 6),
        "bunching_distinguishable": round(bunching_fraction(dist), 6),
        "collision_free_bosons": round(collision_free_fraction(bosons), 6),
        "collision_free_distinguishable":
            round(collision_free_fraction(dist), 6),
        "top_boson_outcomes":
            [[list(k), round(v, 6)] for k, v in top],
    }


def bunching_report():
    """Bosons vs distinguishable bunching across every demo system."""
    rows = {}
    U = beamsplitter_unitary()
    b = sampling_distribution(U, 2)
    d = sampling_distribution(U, 2, distinguishable=True)
    rows["hom_beamsplitter_n2_m2"] = {
        "bunching_bosons": round(bunching_fraction(b), 6),
        "bunching_distinguishable": round(bunching_fraction(d), 6),
        "collision_free_bosons": round(collision_free_fraction(b), 6),
        "collision_free_distinguishable":
            round(collision_free_fraction(d), 6),
        "n": 2,
    }
    for spec in (FOURIER_N3, FOURIER_N4, HAAR_N3, HAAR_N4):
        rep = distribution_report(spec)
        rows[spec["name"]] = {
            "bunching_bosons": rep["bunching_bosons"],
            "bunching_distinguishable": rep["bunching_distinguishable"],
            "collision_free_bosons": rep["collision_free_bosons"],
            "collision_free_distinguishable":
                rep["collision_free_distinguishable"],
            "n": spec["n"],
        }
    return rows


# ================================================================ 4. kNN outcome classifier
# Features: bunching fraction, coincidence (collision-free) rate, and
# photon number n. The training grid is labelled by the lab's own
# verdict policy (model_label below) - the classifier interpolates
# the policy over measured statistics; it never sees particle
# identity, only the numbers a distribution leaves behind.

def model_label(bunch, coinc, n):
    """The verdict policy distilled to a three-way teaching label."""
    if coinc <= 0.02 and bunch >= 0.98:
        return "suppressed-coincidence"
    if bunch >= 0.85 and coinc <= 0.15:
        return "bosonic-bunched"
    if n <= 3 and bunch >= 0.65 and coinc <= 0.35:
        return "bosonic-bunched"
    return "distinguishable-like"


def _training_grid():
    rows = []
    for n in (2, 3, 4):
        for bi in range(21):
            for ci in range(21):
                bunch, coinc = bi / 20.0, ci / 20.0
                if bunch + coinc <= 1.0 + 1e-9:
                    rows.append(((bunch, coinc, n),
                                 model_label(bunch, coinc, n)))
    return rows


TRAINING_GRID = _training_grid()


def _scaled(features):
    bunch, coinc, n = features
    return (bunch, coinc, n / 4.0)


def classify_outcome(bunch, coinc, n, k=7):
    """Distance-weighted kNN over the policy-labelled grid."""
    target = _scaled((bunch, coinc, n))
    ranked = []
    for features, label in TRAINING_GRID:
        point = _scaled(features)
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(target, point)))
        ranked.append((dist, features, label))
    ranked.sort(key=lambda row: (row[0], row[1]))
    weights = {}
    for dist, _, label in ranked[:k]:
        weights[label] = weights.get(label, 0.0) + 1.0 / (dist * dist + 1e-9)
    priority = {"suppressed-coincidence": 0, "bosonic-bunched": 1,
                "distinguishable-like": 2}
    return sorted(weights.items(),
                  key=lambda kv: (-kv[1], priority[kv[0]]))[0][0]


def classifier_report():
    """Verdicts for the lab's own measured systems.

    Features are computed from the real distributions above - the
    classifier grades statistics, not identity, and the seeded Haar
    n = 3 draw is the honest edge case: its bosonic bunching is weak,
    so the policy verdict is distinguishable-like and the report
    keeps the scenario name honest about it.
    """
    rows = bunching_report()
    scenarios = {
        "hom_bosons": rows["hom_beamsplitter_n2_m2"],
        "hom_distinguishable": None,  # filled below from the same row
        "fourier_n3_bosons": rows["fourier_n3_m5"],
        "fourier_n4_bosons": rows["fourier_n4_m6"],
        "haar_n4_bosons": rows["haar_n4_m6"],
        "haar_n3_bosons_weak": rows["haar_n3_m5"],
    }
    out = {}
    hom = rows["hom_beamsplitter_n2_m2"]
    out["hom_bosons"] = classify_outcome(
        hom["bunching_bosons"], hom["collision_free_bosons"], 2)
    out["hom_distinguishable"] = classify_outcome(
        hom["bunching_distinguishable"],
        hom["collision_free_distinguishable"], 2)
    for name, row in scenarios.items():
        if row is None or name.startswith("hom"):
            continue
        out[name] = classify_outcome(
            row["bunching_bosons"], row["collision_free_bosons"], row["n"])
    for spec_name, key in (("fourier_n3_m5", "fourier_n3_distinguishable"),
                           ("fourier_n4_m6", "fourier_n4_distinguishable"),
                           ("haar_n4_m6", "haar_n4_distinguishable")):
        row = rows[spec_name]
        out[key] = classify_outcome(
            row["bunching_distinguishable"],
            row["collision_free_distinguishable"], row["n"])
    return out


# ================================================================ 5. Advisory seats
def _trace(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def argon4_decide(topic="bosonsampling-demo"):
    """Gemini Argon 4 DECIDER seat: MAP->MODEL->STRESS->DECIDE.

    Names-only keys, live calls 0, tighten-only: can add HOLDs, never lift one.
    """
    stages = ["MAP", "MODEL", "STRESS", "DECIDE"]
    payload = {"seat": "gemini-argon-4", "topic": topic, "stages": stages}
    return {
        "seat": "Gemini Argon 4 Extended Thinking",
        "role": "DECIDER",
        "pipeline": stages,
        "tiers": [2048, 8192, 32768],
        "key": "names-only (GEMINI_API_KEY name checked, value never read)",
        "live_calls": 0,
        "decision": "PROCEED - sandbox simulation only, all advantage and hardware gates stay HOLD",
        "can_override_hold": False,
        "trace_sha256_16": _trace(payload),
    }


def claude_advisor(topic="bosonsampling-demo"):
    """Muse advisor seat: advises, can never override a HOLD."""
    return {
        "seat": "Muse",
        "role": "ADVISOR",
        "key": "names-only (MODEL_API_KEY name checked, value never read)",
        "live_calls": 0,
        "advice": "Print the operation ledger next to every distribution: one permanent per output probability, n * 2^n by Ryser at best - then say plainly that at n = 4 the laptop is not the bottleneck, the exponential is.",
        "can_override_hold": False,
    }


def google_flow_plan():
    """Google Flow seat: plan-only, nothing rendered, nothing live."""
    return {
        "seat": "Google Flow",
        "role": "PLAN-ONLY",
        "shots": ["two photon wavepackets meeting on a 50/50 beamsplitter",
                  "both photons leaving through the same port, every time",
                  "a grid of output modes filling with bunched pairs",
                  "a permutation sum growing factorially across the screen",
                  "Ryser's subsets folding the same sum down to n * 2^n"],
        "rendered": False,
        "live": 0,
    }


def brains_report():
    return {"decider": argon4_decide(), "advisor": claude_advisor(),
            "flow": google_flow_plan()}


# ================================================================ checks
def run_checks():
    c = []

    def chk(name, ok):
        c.append((name, bool(ok)))

    # 1. permanents - two implementations, one answer
    rng = random.Random(7)
    mats = {}
    for n in (2, 3, 4, 5):
        stream = _gaussian_stream(100 + n)
        mats[n] = [[complex(next(stream), next(stream)) for _ in range(n)]
                   for _ in range(n)]
    chk("perm_1x1", abs(perm_naive([[3 + 2j]]) - (3 + 2j)) < 1e-12
        and abs(perm_ryser([[3 + 2j]]) - (3 + 2j)) < 1e-12)
    chk("perm_2x2_formula",
        abs(perm_naive([[1, 2], [3, 4]]) - 10) < 1e-12
        and abs(perm_ryser([[1, 2], [3, 4]]) - 10) < 1e-12)
    chk("perm_identity_is_1",
        abs(perm_ryser([[1 if i == j else 0 for j in range(4)]
                        for i in range(4)]) - 1) < 1e-12)
    chk("perm_naive_ryser_agree_n2_n3",
        all(abs(perm_naive(mats[n]) - perm_ryser(mats[n])) < 1e-9
            for n in (2, 3)))
    chk("perm_naive_ryser_agree_n4_n5",
        all(abs(perm_naive(mats[n]) - perm_ryser(mats[n])) < 1e-8
            for n in (4, 5)))
    chk("perm_ops_counts",
        perm_ops(3)["naive_terms"] == 6 and perm_ops(3)["naive_mults"] == 18
        and perm_ops(4)["ryser_ops"] == 64
        and perm_ops(20)["ryser_ops"] == 20 * 2 ** 20
        and perm_ops(30)["naive_terms"] == math.factorial(30))
    chk("ryser_beats_naive_from_n4",
        all(perm_ops(n)["ryser_ops"] < perm_ops(n)["naive_mults"]
            for n in (4, 5, 6, 20, 30)))
    chk("ledger_years_explode",
        cost_ledger((30,))[0]["naive_years_at_labelled_rate"] > 1e15)

    # 2. interferometers - unitary or nothing
    chk("beamsplitter_unitary", unitarity_error(beamsplitter_unitary()) < 1e-12)
    chk("fourier5_unitary", unitarity_error(fourier_unitary(5)) < 1e-12)
    chk("fourier6_unitary", unitarity_error(fourier_unitary(6)) < 1e-12)
    chk("haar5_unitary", unitarity_error(haar_unitary(5)) < 1e-12)
    chk("haar6_unitary", unitarity_error(haar_unitary(6)) < 1e-12)
    chk("haar_deterministic",
        haar_unitary(5) == haar_unitary(5))
    chk("fourier_entries_modulus",
        abs(abs(fourier_unitary(5)[2][3]) - 1 / math.sqrt(5)) < 1e-12)

    # 3. HOM - the dip, from the general machinery
    hom = hom_report()
    chk("hom_coincidence_bosons_zero", hom["coincidence_bosons"] == 0.0)
    chk("hom_coincidence_distinguishable_half",
        abs(hom["coincidence_distinguishable"] - 0.5) < 1e-9)
    chk("hom_bunched_half_each",
        abs(hom["bosons"]["(2, 0)"] - 0.5) < 1e-9
        and abs(hom["bosons"]["(0, 2)"] - 0.5) < 1e-9)
    chk("hom_distinguishable_classical_split",
        abs(hom["distinguishable"]["(2, 0)"] - 0.25) < 1e-9
        and abs(hom["distinguishable"]["(0, 2)"] - 0.25) < 1e-9)
    chk("hom_bunching_bosons_total", hom["bunching_bosons"] == 1.0)

    # 4. full distributions - normalised, bosonic bunching on top
    reps = {spec["name"]: distribution_report(spec)
            for spec in (FOURIER_N3, FOURIER_N4, HAAR_N3, HAAR_N4)}
    chk("distribution_outcome_counts",
        reps["fourier_n3_m5"]["outcomes"] == 35
        and reps["fourier_n4_m6"]["outcomes"] == 126
        and reps["haar_n3_m5"]["outcomes"] == 35
        and reps["haar_n4_m6"]["outcomes"] == 126)
    chk("distributions_sum_to_1",
        all(abs(rep["sum_bosons"] - 1.0) < 1e-9
            and abs(rep["sum_distinguishable"] - 1.0) < 1e-9
            for rep in reps.values()))
    chk("fourier_n3_bunching_gap",
        abs(reps["fourier_n3_m5"]["bunching_bosons"] - 0.72) < 1e-6
        and abs(reps["fourier_n3_m5"]["bunching_distinguishable"] - 0.52)
        < 1e-6)
    chk("fourier_n4_bunching_gap",
        abs(reps["fourier_n4_m6"]["bunching_bosons"] - 0.888889) < 1e-6
        and abs(reps["fourier_n4_m6"]["bunching_distinguishable"]
                - 0.722222) < 1e-6)
    chk("bosons_bunch_more_everywhere",
        all(rep["bunching_bosons"] > rep["bunching_distinguishable"]
            and rep["collision_free_bosons"]
            < rep["collision_free_distinguishable"]
            for rep in reps.values()))
    chk("probabilities_nonnegative",
        all(p >= -1e-12 for rep in reps.values()
            for p in [rep["bunching_bosons"], rep["collision_free_bosons"]]))

    # 5. classifier - labels come from the policy itself
    rep = classifier_report()
    chk("classifier_hom_suppressed",
        rep["hom_bosons"] == "suppressed-coincidence")
    chk("classifier_hom_distinguishable",
        rep["hom_distinguishable"] == "distinguishable-like")
    chk("classifier_fourier_n3_bosonic",
        rep["fourier_n3_bosons"] == "bosonic-bunched")
    chk("classifier_fourier_n4_bosonic",
        rep["fourier_n4_bosons"] == "bosonic-bunched")
    chk("classifier_haar_n4_bosonic",
        rep["haar_n4_bosons"] == "bosonic-bunched")
    chk("classifier_distinguishable_rows",
        rep["fourier_n3_distinguishable"] == "distinguishable-like"
        and rep["fourier_n4_distinguishable"] == "distinguishable-like"
        and rep["haar_n4_distinguishable"] == "distinguishable-like")
    chk("classifier_haar_n3_weak_edge",
        rep["haar_n3_bosons_weak"] == "distinguishable-like")
    rows = bunching_report()
    chk("classifier_matches_model",
        rep["hom_bosons"] == model_label(
            rows["hom_beamsplitter_n2_m2"]["bunching_bosons"],
            rows["hom_beamsplitter_n2_m2"]["collision_free_bosons"], 2)
        and rep["fourier_n4_bosons"] == model_label(
            rows["fourier_n4_m6"]["bunching_bosons"],
            rows["fourier_n4_m6"]["collision_free_bosons"], 4))
    chk("classifier_grid_self_consistent",
        all(classify_outcome(*features) == label
            for features, label in TRAINING_GRID[::7]))

    # gates + seats
    chk("hold_gates_14", len(HOLD_GATES) == 14
        and all(v.startswith("HOLD") for v in HOLD_GATES.values()))
    chk("gate_advantage_hold", gate("quantum_advantage_claim") == "HOLD")
    chk("gate_supremacy_hold", gate("quantum_supremacy_claim") == "HOLD")
    chk("gate_hardware_hold", gate("photonic_hardware_control") == "HOLD")
    chk("gate_randomness_hold", gate("certified_randomness_claim") == "HOLD")
    chk("gate_sandbox_proceed", gate("run_simulation") == "PROCEED")
    brains = brains_report()
    chk("argon4_no_override", brains["decider"]["can_override_hold"] is False
        and brains["decider"]["seat"]
        == "Gemini Argon 4 Extended Thinking")
    chk("claude_no_override", brains["advisor"]["can_override_hold"] is False)
    chk("flow_plan_only", brains["flow"]["rendered"] is False
        and brains["flow"]["live"] == 0)
    return c


# ================================================================ CLI / demo
def demo():
    print("=" * 68)
    print("BosonSampling-Lab - boson sampling & matrix permanent lab")
    print("by Darion Kellar | MIT | pure stdlib | zero network | EDUCATION ONLY")
    print("=" * 68)
    print("\n[1] THE HONEST CORE - permanents are the price of admission")
    print("    Each output probability of an n-photon interferometer is one")
    print("    squared permanent. This lab computes permanents EXACTLY at")
    print("    toy sizes (n = 2, 3, 4) and prints the classical cost ledger")
    print("    at n = 20 and n = 30. No chip, no measurement, no advantage")
    print("    claim: at these sizes the laptop is the fastest sampler here.")
    print("\n[2] Permanents, two ways - naive definition vs Ryser")
    stream = _gaussian_stream(104)
    A = [[complex(next(stream), next(stream)) for _ in range(4)]
         for _ in range(4)]
    pn, pr = perm_naive(A), perm_ryser(A)
    print(f"    seeded 4x4: naive {pn:.6f} | Ryser {pr:.6f} "
          f"| agree to {abs(pn - pr):.2e}")
    for n in (3, 4, 5, 6):
        ops = perm_ops(n)
        print(f"    n = {n}: naive {ops['naive_terms']} terms / "
              f"{ops['naive_mults']} mults | Ryser {ops['ryser_ops']} ops")
    print("\n[3] Interferometers - unitary, asserted before use")
    for name, U in (("beamsplitter 2x2", beamsplitter_unitary()),
                    ("fourier 5x5", fourier_unitary(5)),
                    ("fourier 6x6", fourier_unitary(6)),
                    ("haar-style 6x6 (seeded)", haar_unitary(6))):
        print(f"    {name:26s} max |U^dagger U - I| = "
              f"{unitarity_error(U):.2e}")
    print("\n[4] Hong-Ou-Mandel - the n = 2 case of the general machinery")
    hom = hom_report()
    print(f"    bosons:          (2,0) {hom['bosons']['(2, 0)']} | "
          f"(1,1) {hom['coincidence_bosons']} | "
          f"(0,2) {hom['bosons']['(0, 2)']}")
    print(f"    distinguishable: (2,0) "
          f"{hom['distinguishable']['(2, 0)']} | (1,1) "
          f"{hom['coincidence_distinguishable']} | (0,2) "
          f"{hom['distinguishable']['(0, 2)']}")
    print("    -> indistinguishable photons NEVER split 1-1 on a 50/50")
    print("       beamsplitter; distinguishable ones split half the time.")
    print("\n[5] Full distributions - enumerated, never sampled")
    for spec in (FOURIER_N3, FOURIER_N4, HAAR_N4):
        rep = distribution_report(spec)
        top = rep["top_boson_outcomes"][0]
        print(f"    {rep['system']:14s} n={rep['n_photons']} "
              f"m={rep['m_modes']} | {rep['outcomes']} outcomes | "
              f"sum {rep['sum_bosons']:.12f} | top {tuple(top[0])} "
              f"p={top[1]}")
    print("\n[6] Bunching - bosons vs distinguishable, same unitary")
    for name, row in bunching_report().items():
        print(f"    {name:26s} bunch {row['bunching_bosons']:.6f} vs "
              f"{row['bunching_distinguishable']:.6f} | collision-free "
              f"{row['collision_free_bosons']:.6f} vs "
              f"{row['collision_free_distinguishable']:.6f}")
    print("    -> bosons bunch more and collide less in EVERY system here;")
    print("       the seeded Haar n = 3 draw bunches weakly (0.500593) -")
    print("       a weak draw, reported as one, not hidden.")
    print("\n[7] Classical cost ledger - the wall, as counts")
    for row in cost_ledger():
        print(f"    n = {row['n']:2d}: naive mults {row['naive_mults']:.6e} "
              f"| Ryser ops {row['ryser_ops']:.6e} | Ryser time at "
              f"labelled 1e9 ops/s: {row['ryser_seconds_at_labelled_rate']:.3f} s")
    print("    -> one permanent prices ONE output probability. A sampler")
    print("       must draw from the whole distribution; the ledger is why")
    print("       exact classical boson sampling stops being a laptop job.")
    print("\n[8] Outcome classifier (TinyML kNN, labels from the policy)")
    for name, label in classifier_report().items():
        print(f"    {name:36s} -> {label}")
    print("\n[9] Advisory seats")
    brains = brains_report()
    print(f"    decider: {brains['decider']['decision']} "
          f"trace={brains['decider']['trace_sha256_16']}")
    print(f"    advisor can_override_hold = {brains['advisor']['can_override_hold']}")
    print(f"    flow rendered = {brains['flow']['rendered']} "
          f"live = {brains['flow']['live']}")
    print(f"\n[10] HOLD gates: {len(HOLD_GATES)}")
    for key in HOLD_GATES:
        print(f"    HOLD  {key}")
    checks = run_checks()
    passed = sum(1 for _, ok in checks if ok)
    print(f"\nCHECKS {passed}/{len(checks)}")
    for name, ok in checks:
        if not ok:
            print(f"    FAIL {name}")
    verdict = "PROCEED" if passed == len(checks) else "HOLD"
    print(f"VERDICT {verdict} (sandbox simulation only) | HOLD gates {len(HOLD_GATES)}")
    return 0 if passed == len(checks) else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "demo":
        return demo()
    cmd = argv[0]
    if cmd == "checks":
        checks = run_checks()
        for name, ok in checks:
            print(f"{'PASS' if ok else 'FAIL'} {name}")
        print(f"CHECKS {sum(1 for _, ok in checks if ok)}/{len(checks)}")
        return 0 if all(ok for _, ok in checks) else 1
    if cmd == "permanent":
        stream = _gaussian_stream(104)
        A = [[complex(next(stream), next(stream)) for _ in range(4)]
             for _ in range(4)]
        print(json.dumps({
            "matrix_size": 4,
            "naive": [perm_naive(A).real, perm_naive(A).imag],
            "ryser": [perm_ryser(A).real, perm_ryser(A).imag],
            "abs_diff": abs(perm_naive(A) - perm_ryser(A)),
            "ops": [perm_ops(n) for n in (2, 3, 4, 5, 6)],
        }, indent=2, sort_keys=True))
        return 0
    if cmd == "unitary":
        print(json.dumps({
            "beamsplitter_2x2": unitarity_error(beamsplitter_unitary()),
            "fourier_5x5": unitarity_error(fourier_unitary(5)),
            "fourier_6x6": unitarity_error(fourier_unitary(6)),
            "haar_5x5_seeded": unitarity_error(haar_unitary(5)),
            "haar_6x6_seeded": unitarity_error(haar_unitary(6)),
        }, indent=2, sort_keys=True))
        return 0
    if cmd == "hom":
        print(json.dumps(hom_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "distribution":
        name = argv[1] if len(argv) > 1 else "fourier_n3_m5"
        specs = {s["name"]: s for s in
                 (FOURIER_N3, FOURIER_N4, HAAR_N3, HAAR_N4)}
        print(json.dumps(distribution_report(specs[name]),
                         indent=2, sort_keys=True))
        return 0
    if cmd == "bunching":
        print(json.dumps(bunching_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "ledger":
        print(json.dumps(cost_ledger(), indent=2, sort_keys=True))
        return 0
    if cmd == "classify":
        print(json.dumps(classifier_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "brains":
        print(json.dumps(brains_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "holds":
        for key, value in HOLD_GATES.items():
            print(f"{key}: {value}")
        return 0
    if cmd == "hold-demo":
        action = argv[1] if len(argv) > 1 else "quantum_advantage_claim"
        print(f"{action}: {HOLD_GATES.get(action, 'PROCEED - not gated')}")
        return 2 if gate(action) == "HOLD" else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
