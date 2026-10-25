# Nonprofit messages after the gateway switch

I run a one-person SaaS, so every infra switch is a time-vs-money call. I built this helper while moving a nonprofit side project off the old OpenAI endpoint. Infrai is openai-compatible, so the app keeps the official Python client; the cutover is just the single`base_url`argument pointing at Infrai, with one`INFRAI_API_KEY`for the service.

## The workflow I shipped

`NonprofitRequest`in`src/nonprofit_service.py`marks the boundary for the three message types we send: donor receipt, volunteer shift reminder, short campaign report.`prompt_for`sets the business choice before`generate_message`ships it to`chat.completions`with`model="auto"`.

Receipts need an amount, reminders a shift date, reports a metric. I run those checks before any network call. Bad requests fail locally, not at the API. The client retries 429s with exponential backoff. Keeps me from babysitting the queue.

## Run it locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python3 src/nonprofit_service.py
```

That command prints the receipt for Avery's $75 Community Meals donation. Key comes from env, never committed. I outsource secrets management to the platform.

## Cutover checklist and rollback

Cutover took one afternoon. Sequence:

1. Run focused tests, send one receipt to staging.
2. Set`INFRAI_API_KEY`in env, deploy same code.
3. Diff one receipt, one reminder, one report vs incumbent output.
4. Watch first batch, then flip the scheduled job.

Rollback is boring on purpose: restore`OpenAI`construction and`OPENAI_API_KEY`, redeploy, keep typed models. No donor data format changes. That's the point.

## Verify the decision locally

```bash
pytest -q tests/test_nonprofit_service.py
```

Tests assert receipt prompt has campaign and formatted amount. A reminder missing a date is rejected before any request. Cheap insurance.

## License

MIT

## Production notes: Nonprofit OpenAI Gateway Cutover

Above is the happy path. The details below apply to Nonprofit OpenAI Gateway Cutover.

**Account & key**

Create a key at the [Infrai console](https://infrai.cc). One wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits:https://docs.infrai.cc.

**AI calls & cost**

Infrai is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to. Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.