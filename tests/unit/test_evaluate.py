"""Tests for metric calculations with hand-computed confusion matrices."""

from benchmarks.evaluate import ConfusionMatrix, _wilson_ci


def test_perfect_precision() -> None:
    m = ConfusionMatrix(tp=10, fp=0, fn=2, tn=5)
    assert m.precision == 1.0


def test_perfect_recall() -> None:
    m = ConfusionMatrix(tp=10, fp=3, fn=0, tn=5)
    assert m.recall == 1.0


def test_known_values() -> None:
    m = ConfusionMatrix(tp=8, fp=2, fn=2, tn=8)
    assert abs(m.precision - 0.8) < 1e-9
    assert abs(m.recall - 0.8) < 1e-9
    assert abs(m.fpr - 0.2) < 1e-9


def test_f1() -> None:
    m = ConfusionMatrix(tp=8, fp=2, fn=2, tn=8)
    assert abs(m.f1 - 0.8) < 1e-9


def test_zero_division() -> None:
    m = ConfusionMatrix()
    assert m.precision == 0.0
    assert m.recall == 0.0
    assert m.fpr == 0.0
    assert m.f1 == 0.0


def test_wilson_ci_bounds() -> None:
    lo, hi = _wilson_ci(8, 10)
    assert 0.0 <= lo <= hi <= 1.0
    assert lo > 0.4
    assert hi < 1.0
