"""Tests for maps constants, specifically ICPE rubriques classification."""

import pytest

from maps.constants import ANNUAL_ICPE_RUBRIQUES, DAILY_ICPE_RUBRIQUES, ICPE_RUBRIQUES


class TestICPERubriquesClassification:
    """Test suite for ICPE rubriques classification."""

    def test_annual_rubriques_contains_expected_values(self):
        """Test that ANNUAL_ICPE_RUBRIQUES contains 2760-1, 2760-2, 2790, and 2791."""
        assert "2760-1" in ANNUAL_ICPE_RUBRIQUES
        assert "2760-2" in ANNUAL_ICPE_RUBRIQUES
        assert "2790" in ANNUAL_ICPE_RUBRIQUES
        assert "2791" in ANNUAL_ICPE_RUBRIQUES
        assert len(ANNUAL_ICPE_RUBRIQUES) == 4

    def test_daily_rubriques_contains_expected_values(self):
        """Test that DAILY_ICPE_RUBRIQUES contains 2770 and 2771."""
        assert "2770" in DAILY_ICPE_RUBRIQUES
        assert "2771" in DAILY_ICPE_RUBRIQUES
        assert len(DAILY_ICPE_RUBRIQUES) == 2

    def test_icpe_rubriques_is_union_of_annual_and_daily(self):
        """Test that ICPE_RUBRIQUES is the union of ANNUAL and DAILY rubriques."""
        expected = set(ANNUAL_ICPE_RUBRIQUES) | set(DAILY_ICPE_RUBRIQUES)
        assert set(ICPE_RUBRIQUES) == expected

    def test_no_overlap_between_annual_and_daily(self):
        """Test that there is no overlap between ANNUAL and DAILY rubriques."""
        overlap = set(ANNUAL_ICPE_RUBRIQUES) & set(DAILY_ICPE_RUBRIQUES)
        assert len(overlap) == 0, f"Unexpected overlap: {overlap}"

    @pytest.mark.parametrize(
        "rubrique,expected_type",
        [
            ("2760-1", "annual"),
            ("2760-2", "annual"),
            ("2790", "annual"),
            ("2791", "annual"),
            ("2770", "daily"),
            ("2771", "daily"),
        ],
    )
    def test_rubrique_classification(self, rubrique, expected_type):
        """Test that each rubrique is correctly classified."""
        if expected_type == "annual":
            assert rubrique in ANNUAL_ICPE_RUBRIQUES
            assert rubrique not in DAILY_ICPE_RUBRIQUES
        else:
            assert rubrique in DAILY_ICPE_RUBRIQUES
            assert rubrique not in ANNUAL_ICPE_RUBRIQUES

    def test_2791_is_annual_like_2790(self):
        """Test that 2791 has the same classification as 2790 (both annual)."""
        assert ("2790" in ANNUAL_ICPE_RUBRIQUES) == ("2791" in ANNUAL_ICPE_RUBRIQUES)
        assert ("2790" in DAILY_ICPE_RUBRIQUES) == ("2791" in DAILY_ICPE_RUBRIQUES)
