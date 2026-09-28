import pytest

from app.checks.checks import CheckResult, aggregate


class TestAggregate:
    @pytest.mark.parametrize(
        "first, second, expected_ok",
        [
            pytest.param(True, True, True, id="both ok"),
            pytest.param(True, False, False, id="first ok, second not ok"),
            pytest.param(False, True, False, id="first not ok, second ok"),
            pytest.param(False, False, False, id="both not ok"),
        ],
    )
    def test_ok_matrix(self, first: bool, second: bool, expected_ok: bool) -> None:
        ## GIVEN: two CheckResults with the given ok flags
        results = [
            CheckResult(name="first", ok=first),
            CheckResult(name="second", ok=second),
        ]

        ## WHEN: aggregate is called
        aggregated = aggregate(*results)

        ## THEN: ok is the logical AND of all inputs, and per-check order is preserved
        assert aggregated.ok is expected_ok
        assert [c.name for c in aggregated.checks] == ["first", "second"]

    def test_all_ok_returns_ok_true(self) -> None:
        ## GIVEN: a set of CheckResults all with ok=True
        results = [
            CheckResult(name="kafka", ok=True),
            CheckResult(name="db", ok=True),
        ]

        ## WHEN: aggregate is called
        aggregated = aggregate(*results)

        ## THEN: the AggregateResponse has ok=True and the checks in order
        assert aggregated.ok is True
        assert [c.name for c in aggregated.checks] == ["kafka", "db"]

    def test_any_failure_returns_ok_false(self) -> None:
        ## GIVEN: at least one CheckResult with ok=False
        results = [
            CheckResult(name="kafka", ok=True),
            CheckResult(name="db", ok=False, detail="connection refused"),
        ]

        ## WHEN: aggregate is called
        aggregated = aggregate(*results)

        ## THEN: ok=False, and per-check detail preserved
        assert aggregated.ok is False
        assert aggregated.checks[1].detail == "connection refused"

    def test_empty_returns_ok_true(self) -> None:
        ## GIVEN: no results
        ## WHEN: aggregate is called with no args
        aggregated = aggregate()

        ## THEN: ok=True (all() on empty iterable), checks=[]
        assert aggregated.ok is True
        assert aggregated.checks == []
