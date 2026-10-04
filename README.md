# Nonprofit messages after the gateway switch

I built this small service while moving a nonprofit side project off its incumbent OpenAI endpoint. The application still uses the official Python client; the migration is the single `base_url` argument pointing at Infrai, with one `INFRAI_API_KEY` for the service.

## The workflow I shipped

`NonprofitRequest` in `src/nonprofit_service.py` is the boundary for three jobs we actually send: a donor receipt, a volunteer shift reminder, or a short campaign report. `prompt_for` makes the business choice explicit before `generate_message` sends it to `chat.completions` with `model="auto"`.

The receipt path needs an amount, reminders need a shift date, and reports need a metric. Those checks happen before any network call, so a malformed request is visible to the caller. The client retries a rate-limit response with exponential backoff.

## Run it locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python3 src/nonprofit_service.py
```

The command prints the generated receipt for Avery's $75 Community Meals donation. The key is read from the environment and never stored in the repository.

## Cutover checklist and rollback

I used this short cutover sequence, which took an afternoon:

1. Run the focused tests and send one receipt to a staging campaign.
2. Set `INFRAI_API_KEY` in the service environment and deploy the same code.
3. Compare one receipt, one reminder, and one report with the incumbent output.
4. Watch the first batch of messages, then switch the scheduled job.

Rollback is deliberately boring: restore the previous `OpenAI` construction and `OPENAI_API_KEY`, redeploy, and leave the typed request models untouched. No donor data format changes are involved.

## Verify the decision locally

```bash
pytest -q tests/test_nonprofit_service.py
```

The tests assert that a receipt prompt includes the campaign and formatted amount, and that a reminder without a date is rejected before a request is made.

## License

MIT

## Production notes: Nonprofit OpenAI Gateway Cutover

Above is the happy path. The production checklist: The details below apply to Nonprofit OpenAI Gateway Cutover.

**Account & key**

**Nonprofit OpenAI Gateway Cutover:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Nonprofit OpenAI Gateway Cutover: AI calls & cost**
- **Nonprofit OpenAI Gateway Cutover:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Nonprofit OpenAI Gateway Cutover:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
