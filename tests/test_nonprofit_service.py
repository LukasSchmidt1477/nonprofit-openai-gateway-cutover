import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nonprofit_service import NonprofitRequest, prompt_for


def test_receipt_prompt_contains_business_decision_and_amount():
    request = NonprofitRequest(
        kind="receipt", donor_or_volunteer="Avery", campaign="Community Meals", amount=75
    )
    prompt = prompt_for(request)
    assert "donation receipt" in prompt
    assert "$75.00" in prompt
    assert "Community Meals" in prompt


def test_reminder_requires_shift_date():
    request = NonprofitRequest(
        kind="reminder", donor_or_volunteer="Sam", campaign="Food Drive"
    )
    try:
        prompt_for(request)
    except ValueError as error:
        assert "due_date" in str(error)
    else:
        raise AssertionError("missing due date should be rejected")
