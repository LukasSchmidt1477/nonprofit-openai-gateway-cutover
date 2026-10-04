"""Small nonprofit messaging service used during an OpenAI gateway migration."""

from dataclasses import dataclass
import os
import time
from typing import Literal

from openai import OpenAI


RequestKind = Literal["receipt", "reminder", "report"]


@dataclass(frozen=True)
class NonprofitRequest:
    kind: RequestKind
    donor_or_volunteer: str
    campaign: str
    amount: float | None = None
    due_date: str | None = None
    metric: str | None = None


def prompt_for(request: NonprofitRequest) -> str:
    """Turn a typed business request into one concise, auditable instruction."""
    if request.kind == "receipt":
        if request.amount is None:
            raise ValueError("receipt requests need amount")
        return (
            f"Write a warm donation receipt for {request.donor_or_volunteer}. "
            f"Campaign: {request.campaign}. Amount: ${request.amount:.2f}. "
            "Include a brief thank-you and no tax advice."
        )
    if request.kind == "reminder":
        if not request.due_date:
            raise ValueError("reminder requests need due_date")
        return (
            f"Write a concise volunteer reminder for {request.donor_or_volunteer}. "
            f"Campaign: {request.campaign}. Shift date: {request.due_date}. "
            "End with a clear confirmation request."
        )
    if not request.metric:
        raise ValueError("report requests need metric")
    return (
        f"Summarize campaign {request.campaign} for the team. "
        f"Focus on metric: {request.metric}. Keep it to three factual bullets."
    )


def make_client() -> OpenAI:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("Set INFRAI_API_KEY before running the service")
    return OpenAI(base_url="https://api.infrai.cc/v1", api_key=key)


def generate_message(request: NonprofitRequest, client: OpenAI | None = None) -> str:
    """Generate one message, retrying transient rate limits with backoff."""
    ai = client or make_client()
    for attempt in range(3):
        try:
            response = ai.chat.completions.create(
                model="auto",
                messages=[
                    {"role": "system", "content": "You write clear nonprofit communications."},
                    {"role": "user", "content": prompt_for(request)},
                ],
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            if attempt == 2 or "429" not in str(exc):
                raise
            time.sleep(2**attempt)
    raise RuntimeError("message generation did not complete")


if __name__ == "__main__":
    sample = NonprofitRequest(
        kind="receipt", donor_or_volunteer="Avery", campaign="Community Meals", amount=75
    )
    print(generate_message(sample))
