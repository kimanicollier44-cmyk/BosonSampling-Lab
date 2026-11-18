"""Tests for BosonSampling-Lab: permanents, unitaries, HOM, distributions."""
import math

import pytest

import main as m


# ---- permanents
def test_perm_known_values():
    assert abs(m.perm_naive([[5]]) - 5) < 1e-12
    assert abs(m.perm_naive([[1, 2], [3, 4]]) - 10) < 1e-12
    assert abs(m.perm_ryser([[1, 2], [3, 4]]) - 10) < 1e-12
    ident = [[1 if i == j else 0 for j in range(4)] for i in range(4)]
    assert abs(m.perm_ryser(ident) - 1) < 1e-12
    ones = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
    assert abs(m.perm_naive(ones) - 6) < 1e-12  # 3! permutations


@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_perm_naive_ryser_agree(n):
    stream = m._gaussian_stream(100 + n)
    A = [[complex(next(stream), next(stream)) for _ in range(n)]
         for _ in range(n)]
    assert abs(m.perm_naive(A) - m.perm_ryser(A)) < 1e-8


def test_perm_ops_counts():
    assert m.perm_ops(3) == {"n": 3, "naive_terms": 6,
                             "naive_mults": 18, "ryser_ops": 24}
    assert m.perm_ops(4)["ryser_ops"] == 64
    assert m.perm_ops(20)["ryser_ops"] == 20 * 2 ** 20
    assert m.perm_ops(30)["naive_terms"] == math.factorial(30)


def test_ryser_wins_from_n4():
    for n in (4, 5, 6, 20, 30):
        ops = m.perm_ops(n)
        assert ops["ryser_ops"] < ops["naive_mults"]


def test_ledger_shape():
    rows = m.cost_ledger()
    assert [r["n"] for r in rows] == [2, 3, 4, 5, 6, 20, 30]
    assert rows[-1]["naive_years_at_labelled_rate"] > 1e15
    assert rows[-1]["ryser_seconds_at_labelled_rate"] == pytest.approx(
        30 * 2 ** 30 / 1e9, rel=1e-9)


# ---- interferometers
@pytest.mark.parametrize("build", [
    lambda: m.beamsplitter_unitary(),
    lambda: m.fourier_unitary(5),
    lambda: m.fourier_unitary(6),
    lambda: m.haar_unitary(5),
    lambda: m.haar_unitary(6),
])
def test_unitaries_are_unitary(build):
    assert m.unitarity_error(build()) < 1e-12


def test_haar_deterministic():
    assert m.haar_unitary(6) == m.haar_unitary(6)
    assert m.haar_unitary(6) != m.haar_unitary(6, seed=1)


def test_fourier_modulus():
    U = m.fourier_unitary(5)
    assert all(abs(abs(x) - 1 / math.sqrt(5)) < 1e-12
               for row in U for x in row)


# ---- Hong-Ou-Mandel
def test_hom_bosons_never_split():
    rep = m.hom_report()
    assert rep["coincidence_bosons"] == 0.0
    assert rep["bosons"]["(2, 0)"] == pytest.approx(0.5)
    assert rep["bosons"]["(0, 2)"] == pytest.approx(0.5)
    assert rep["bunching_bosons"] == 1.0


def test_hom_distinguishable_classical():
    rep = m.hom_report()
    assert rep["coincidence_distinguishable"] == pytest.approx(0.5)
    assert rep["distinguishable"]["(2, 0)"] == pytest.approx(0.25)
    assert rep["distinguishable"]["(0, 2)"] == pytest.approx(0.25)


# ---- distributions
@pytest.mark.parametrize("spec,outcomes", [
    (m.FOURIER_N3, 35), (m.FOURIER_N4, 126),
    (m.HAAR_N3, 35), (m.HAAR_N4, 126),
])
def test_distribution_normalised(spec, outcomes):
    rep = m.distribution_report(spec)
    assert rep["outcomes"] == outcomes
    assert rep["sum_bosons"] == pytest.approx(1.0, abs=1e-9)
    assert rep["sum_distinguishable"] == pytest.approx(1.0, abs=1e-9)


def test_fourier_bunching_values():
    rep3 = m.distribution_report(m.FOURIER_N3)
    assert rep3["bunching_bosons"] == pytest.approx(0.72, abs=1e-6)
    assert rep3["bunching_distinguishable"] == pytest.approx(0.52, abs=1e-6)
    rep4 = m.distribution_report(m.FOURIER_N4)
    assert rep4["bunching_bosons"] == pytest.approx(0.888889, abs=1e-6)
    assert rep4["bunching_distinguishable"] == pytest.approx(
        0.722222, abs=1e-6)


def test_bosons_bunch_more():
    for spec in (m.FOURIER_N3, m.FOURIER_N4, m.HAAR_N3, m.HAAR_N4):
        rep = m.distribution_report(spec)
        assert rep["bunching_bosons"] > rep["bunching_distinguishable"]
        assert (rep["collision_free_bosons"]
                < rep["collision_free_distinguishable"])


def test_occupations_count():
    assert len(list(m.occupations(3, 5))) == 35
    assert len(list(m.occupations(4, 6))) == 126
    assert all(sum(t) == 4 for t in m.occupations(4, 6))


# ---- classifier
def test_classifier_scenarios():
    rep = m.classifier_report()
    assert rep["hom_bosons"] == "suppressed-coincidence"
    assert rep["hom_distinguishable"] == "distinguishable-like"
    assert rep["fourier_n3_bosons"] == "bosonic-bunched"
    assert rep["fourier_n4_bosons"] == "bosonic-bunched"
    assert rep["haar_n4_bosons"] == "bosonic-bunched"
    assert rep["fourier_n3_distinguishable"] == "distinguishable-like"
    assert rep["fourier_n4_distinguishable"] == "distinguishable-like"
    assert rep["haar_n4_distinguishable"] == "distinguishable-like"
    assert rep["haar_n3_bosons_weak"] == "distinguishable-like"


def test_classifier_matches_policy_on_grid():
    for features, label in m.TRAINING_GRID[::7]:
        assert m.classify_outcome(*features) == label


def test_model_label_corners():
    assert m.model_label(1.0, 0.0, 2) == "suppressed-coincidence"
    assert m.model_label(0.9, 0.1, 4) == "bosonic-bunched"
    assert m.model_label(0.5, 0.5, 2) == "distinguishable-like"


# ---- gates + seats
def test_hold_gates():
    assert len(m.HOLD_GATES) == 14
    assert all(v.startswith("HOLD") for v in m.HOLD_GATES.values())
    assert m.gate("quantum_advantage_claim") == "HOLD"
    assert m.gate("quantum_supremacy_claim") == "HOLD"
    assert m.gate("certified_randomness_claim") == "HOLD"
    assert m.gate("run_simulation") == "PROCEED"


def test_seats_never_override():
    brains = m.brains_report()
    assert brains["decider"]["seat"] == "Gemini Argon 4 Extended Thinking"
    assert brains["decider"]["can_override_hold"] is False
    assert brains["advisor"]["can_override_hold"] is False
    assert brains["flow"]["rendered"] is False
    assert brains["flow"]["live"] == 0


# ---- CLI
def test_cli_exit_codes():
    assert m.main(["checks"]) == 0
    assert m.main(["hom"]) == 0
    assert m.main(["ledger"]) == 0
    assert m.main(["classify"]) == 0
    assert m.main(["hold-demo"]) == 2
    assert m.main(["hold-demo", "photonic_hardware_control"]) == 2
    assert m.main(["hold-demo", "run_simulation"]) == 0


def test_demo_deterministic(capsys):
    assert m.demo() == 0
    first = capsys.readouterr().out
    assert m.demo() == 0
    second = capsys.readouterr().out
    assert first == second
    assert "CHECKS 44/44" in first
