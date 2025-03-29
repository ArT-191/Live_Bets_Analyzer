import pytest
import time
import json
from processor import (
    calculate_true_odds,
    calculate_median,
    calculate_roi,
    process,
    get_matches_state
)

# --- TrueOdds ----------------------------------------------------------------
def test_calculate_true_odds():
    assert calculate_true_odds(2.0) == round(2.0 / (1 - 0.08), 4)


# --- Median ------------------------------------------------------------------
@pytest.mark.parametrize("values, expected", [
    ([1.5, 2.5, 3.5], 2.5),
    ([1.5, 2.5], 2.0),
    ([], None),
])
def test_calculate_median(values, expected):
    assert calculate_median(values) == expected


# --- ROI ---------------------------------------------------------------------
def test_calculate_roi_positive():
    assert calculate_roi(2.1, 2.0) == 5.0

def test_calculate_roi_negative():
    assert calculate_roi(1.8, 2.0) == -10.0

def test_calculate_roi_zero_division():
    assert calculate_roi(2.0, 0.0) == 0.0


# --- Processing -------------------------------------------------------------
@pytest.mark.asyncio
async def test_process_and_storage_update():
    sample = {
        "MatchId": "test-1",
        "Source": "Testbook",
        "homeName": "Alpha",
        "awayName": "Beta",
        "HomeScore": 1,
        "AwayScore": 0,
        "Periods": [
            {
                "Totals": {
                    "2.5": {"WinMore": 1.95, "WinLess": 1.85},
                    "3.5": {"WinMore": 2.1, "WinLess": 1.7}
                }
            }
        ]
    }

    await process(json.dumps(sample))

    state = get_matches_state()
    assert "test-1" in state

    match = state["test-1"]
    assert match["home"] == "Alpha"
    assert match["away"] == "Beta"
    assert match["score"] == "1:0"
    assert "2.5" in match["outcomes"]
    assert "Testbook" in match["outcomes"]["2.5"]["bookmakers"]

    bookmaker_data = match["outcomes"]["2.5"]["bookmakers"]["Testbook"]
    assert bookmaker_data["WinMore"] == 1.95
    assert bookmaker_data["WinLess"] == 1.85
    assert "ROI_More" in bookmaker_data
    assert "ROI_Less" in bookmaker_data
