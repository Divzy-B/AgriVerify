# Bolna Voice Provider Setup

## Status in this repository

The Bolna provider adapter, generic provider interface, webhook normalization,
idempotency constraints, and local text simulation are implemented. No live
phone call was made from this repository: no Bolna account credentials or
telephone configuration were supplied.

## Step-by-step checklist (first live call)

Do the steps in order. **You** = needs your accounts or machine. Items marked
*unverified* are not covered by Bolna's public docs as of 2026-10-29; the first
test call settles them (step 14).

### A. Prepare the backend (You)

1. [ ] Register a test farmer and field in the dashboard (**Register Farm**), using
   **your own mobile number with the country code**, for example `+91 98765 43210`.
   The field can be anywhere; in demo mode it gets no satellite data.
2. [ ] Generate a fresh webhook secret (the one in git history is exposed):
   `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Put it in `.env`
   as `BOLNA_WEBHOOK_SECRET`.
3. [ ] Keep `AGRIVERIFY_DEMO_MODE=true` for the first call (tests the call flow
   without satellite access; the verdict will be `INSUFFICIENT_EVIDENCE` for a new
   field). Set it to `false` later to use real imagery.
4. [ ] Start the backend: from `backend/`, `uvicorn app.main:app --port 8000`.
5. [ ] Open a public HTTPS tunnel to it, for example `ngrok http 8000`. Note the
   `https://<PUBLIC_HOST>` address. Open `https://<PUBLIC_HOST>/api/v1/health` in a
   browser to confirm it answers. Keep the tunnel's request inspector open
   (ngrok: `http://127.0.0.1:4040`).
6. [ ] *Optional:* if you restrict inbound IPs, allow Bolna's source addresses
   listed in its docs (13.203.39.153, 13.126.9.249, 13.202.133.53 at the time of
   writing; check the docs).

### B. Create the agent in Bolna (You)

7. [ ] Create a Bolna account. Under **Developers > API Keys** create a key and put
   it in `.env` as `BOLNA_API_KEY`.
8. [ ] Create an agent. Paste `backend/app/voice/prompts/farmer_intake.md` as the
   agent prompt. Choose English for the first test. Keep `{from_number}` and
   `{execution_id}` as written in the prompt. **For an outbound test call** (Bolna
   calls your phone) replace `{from_number}` with `{to_number}`: on an outbound call
   `from_number` is the agent's number, not the farmer's.
9. [ ] In the agent's **Tools** tab choose **Write manually** and add the four tools
   below, one at a time. Replace `<PUBLIC_HOST>` and `<SECRET>`. The tool `name`
   values must stay exactly as written; the prompt refers to them.
10. [ ] Set the agent's webhook (the docs call it the *Extractions* tab; the repo's
    earlier notes say the same) to `https://<PUBLIC_HOST>/api/v1/voice/webhooks/bolna`,
    with the custom header `X-Webhook-Secret: <SECRET>`, for at least the
    `completed` status.
11. [ ] Copy the agent's id into `.env` as `BOLNA_AGENT_ID`, then restart the backend
    so it picks up the new `.env`.
12. [ ] Get a way to call: for the first test either place an **outbound test call**
    from the Bolna dashboard to your own phone, or attach a phone number for
    inbound calls (Bolna's *Inbound* tab).

### C. Test and check (You, with Claude reading the results)

13. [ ] Make the call. Say the planting date with the year, for example "25 May 2025".
14. [ ] **During and after the call, read the tunnel inspector.** Confirm for each
    tool request: (a) the body is **JSON**; (b) the header `X-Webhook-Secret` is
    present; (c) `phone_number` is your number and `session_id` is the call's
    execution id, not a placeholder or empty. Use the failure table below.
15. [ ] In the dashboard: **Claims** shows a new claim; **AI Verification Calls**
    shows the session with its transcript, and the session is linked to the claim.
16. [ ] Repeat once with a wrong date format ("May 25" with no year) and confirm the
    agent asks again instead of failing.
17. [ ] Only then try Hindi (see Language validation). Record what you found in
    `docs/decision.md`.

### Tool definitions to paste (step 9)

Bolna's custom-function format is a JSON object with `name`, `description`,
`pre_call_message`, `parameters`, `key: "custom_task"` and a `value` block
(`method`, `url`, `param`, optional `api_token`, `headers`). `%(name)s` passes a
parameter into the request. *Unverified:* the `headers` format, that the body is
sent as JSON, and that variables work inside `param`. That last point is why the
prompt tells the agent to copy `{from_number}` and `{execution_id}` into the
parameters itself.

```json
{
  "name": "lookup_farmer",
  "description": "Find the caller's registered farmer record and fields from their phone number. Call this first.",
  "pre_call_message": "One moment while I find your record.",
  "parameters": {"type": "object", "properties": {
    "phone_number": {"type": "string", "description": "The farmer's phone number, copied exactly from the call details."}
  }, "required": ["phone_number"]},
  "key": "custom_task",
  "value": {"method": "POST", "url": "https://<PUBLIC_HOST>/api/v1/voice/tools/lookup-farmer",
    "headers": {"X-Webhook-Secret": "<SECRET>"}, "param": {"phone_number": "%(phone_number)s"}}
}
```

```json
{
  "name": "create_claim",
  "description": "Record the caller's confirmed planting date for one of their fields. Call only after the caller confirmed the field and the date.",
  "pre_call_message": "Let me record that.",
  "parameters": {"type": "object", "properties": {
    "phone_number": {"type": "string", "description": "The farmer's phone number from the call details."},
    "farm_id": {"type": "string", "description": "The farm_id of the chosen field, taken from the lookup_farmer result."},
    "crop_type": {"type": "string", "description": "The crop on the field record."},
    "planting_date": {"type": "string", "description": "The confirmed planting date as YYYY-MM-DD, including the year."},
    "session_id": {"type": "string", "description": "The call id from the call details."}
  }, "required": ["phone_number", "farm_id", "planting_date", "session_id"]},
  "key": "custom_task",
  "value": {"method": "POST", "url": "https://<PUBLIC_HOST>/api/v1/voice/tools/create-claim",
    "headers": {"X-Webhook-Secret": "<SECRET>"},
    "param": {"phone_number": "%(phone_number)s", "farm_id": "%(farm_id)s", "crop_type": "%(crop_type)s", "planting_date": "%(planting_date)s", "session_id": "%(session_id)s"}}
}
```

```json
{
  "name": "run_verification",
  "description": "Check the recorded planting date against satellite evidence and return the result to explain to the caller. Call right after create_claim.",
  "pre_call_message": "I am checking that against the satellite records now.",
  "parameters": {"type": "object", "properties": {
    "farm_id": {"type": "string", "description": "The same farm_id used in create_claim."},
    "session_id": {"type": "string", "description": "The call id from the call details."}
  }, "required": ["farm_id", "session_id"]},
  "key": "custom_task",
  "value": {"method": "POST", "url": "https://<PUBLIC_HOST>/api/v1/voice/tools/run-verification",
    "headers": {"X-Webhook-Secret": "<SECRET>"}, "param": {"farm_id": "%(farm_id)s", "session_id": "%(session_id)s"}}
}
```

```json
{
  "name": "request_human_review",
  "description": "Ask a human insurance reviewer to look at this claim. Use when the evidence is weak or the caller disputes the result.",
  "pre_call_message": "I will ask a reviewer to look at this.",
  "parameters": {"type": "object", "properties": {
    "claim_id": {"type": "string", "description": "The claim_id returned by create_claim."}
  }, "required": ["claim_id"]},
  "key": "custom_task",
  "value": {"method": "POST", "url": "https://<PUBLIC_HOST>/api/v1/voice/tools/request-human-review",
    "headers": {"X-Webhook-Secret": "<SECRET>"}, "param": {"claim_id": "%(claim_id)s"}}
}
```

### When something fails

| What you see | Likely cause | Fix |
|---|---|---|
| Tool returns `401` | The secret header was not sent, or has a different value | Check the `headers` format in Bolna and that `.env` matches; restart the backend after editing `.env` |
| `422` and the inspector shows an empty or form-encoded body | Bolna is not sending JSON | Tell Claude; the server can accept form data |
| `422` "not registered to the phone number" | The agent sent the wrong number: on an outbound call `from_number` is the agent | Use `{to_number}` in the prompt for outbound; check the number has its country code |
| `404` "No farmer is registered" | The number is not registered, or differs by country code | Register the farmer with the country code (step 1) |
| `422` mentioning `session_id` | The agent left the call id empty or a placeholder | Check `{execution_id}` is in the prompt exactly as written |
| Claim exists but the call shows no claim | `session_id` was not Bolna's execution id | Fix the prompt so the tool receives `{execution_id}` |
| Webhook returns `401` | Webhook header not configured | Add `X-Webhook-Secret` in the webhook settings |
| Agent invents a farm id or phone number | The model ignored the instructions | Tighten the prompt or choose a stronger model; check the transcript |

### Later improvement (not built)

Bolna can look up an inbound caller before the call starts and inject the result
into the prompt (its *identify incoming callers* feature, which sends the caller's
number to a URL you provide). That would remove the `lookup_farmer` tool call and
stop the model copying identifiers, at the cost of a new endpoint. Consider it if
the first calls show the model mishandling the phone number or call id.

## Configure an agent

1. Create an API key in **Bolna Dashboard → Developers → API Keys** and store
   it only in `BOLNA_API_KEY`.
2. Create or select the production agent, configure its voice/transcriber/LLM
   and agent prompt, and assign its ID to `BOLNA_AGENT_ID`.
3. Copy `backend/app/voice/prompts/farmer_intake.md` into the agent’s system
   behavior, then configure custom function tools that reach AgriVerify’s
   publicly accessible tool endpoints.
4. In the agent’s **Extractions** tab, set the public HTTPS callback to
   `https://<host>/api/v1/voice/webhooks/bolna`, choose the relevant statuses,
   and save the agent. Add an agreed custom header if `BOLNA_WEBHOOK_SECRET`
   is configured locally.
5. Test with non-sensitive demo data and verify the stored Voice Session,
   transcript, claim, and audit event.

The documented outbound call pattern is `POST https://api.bolna.ai/call` with
Bearer authentication, `agent_id`, recipient phone number, optional
`agent_data.language`, and `user_data`. The adapter owns that vendor payload;
the rest of AgriVerify uses generic operations.

## Tool endpoints

Configure the following endpoints in the provider’s custom function-tool
definition, with their documented request schemas:

- `POST /api/v1/voice/tools/lookup-farmer` (body `{phone_number}`)
- `POST /api/v1/voice/tools/lookup-field` (older, by spoken farm id; not used by the current prompt)
- `POST /api/v1/voice/tools/create-claim`
- `POST /api/v1/voice/tools/run-verification`
- `POST /api/v1/voice/tools/request-human-review?claim_id=<id>`

The implementation rejects crop mismatch, requires a confirmed date, and uses
the voice session identifier for idempotent claim creation.

**Caller identification.** The agent identifies the farmer from the caller's
phone number: it calls `lookup-farmer` first and passes the same number as
`phone_number` to `create-claim`, which refuses a field that belongs to a
different farmer. For this to work the tool definitions in Bolna must be
configured to send the caller's number. **TBD, verify in the Bolna dashboard:**
how Bolna exposes the caller's number to a custom function tool (a context
variable or call metadata) for inbound calls, and for outbound calls pass it in
`user_data` from `initiate_call`. Farmers must already be registered
(dashboard, Register Farm) with a phone number that includes the country code.

**Session id.** Configure the tools to send Bolna's call (execution) id as
`session_id`. The server stores the claim under that id and links the call's
voice session to it when the webhook arrives. If a different id is sent, the
claim still works but the transcript is not attached to it. **TBD, verify in
Bolna:** how the call id is exposed to a tool.

**Dates.** The agent should send `planting_date` as `YYYY-MM-DD`; forms such as
`25 May 2025` also work. A date without a year, or a numeric date like
`05/06/2025` that could be day/month or month/day, is refused with a message the
agent should relay and then ask again.

**Secret header.** Every tool call and the webhook must send
`X-Webhook-Secret: <BOLNA_WEBHOOK_SECRET>`. Configure it as a custom header on
each tool definition and on the webhook. When the secret is set on the server
and a request omits it, the server answers `401`.

## Language validation

English is the local simulation default. Bolna documents language selection in
call `agent_data`; configure and live-test Hindi (`hi`) before offering it.
Do not announce Marathi (`mr`) support until the precise agent configuration is
verified in a test call.

## Webhook security

Current Bolna webhook setup documentation describes a callback URL, selectable
statuses, and optional custom headers; it does not establish a signed webhook
secret contract for this integration. Therefore this app does not invent an HMAC
verification scheme. It optionally compares a user-configured custom header,
and a production deployment should also use HTTPS, network allowlists (where
appropriate), a reverse proxy, and strict event logging.

## References

- [Bolna API authentication](https://www.bolna.ai/docs/api-reference/introduction)
- [Bolna webhook setup and status events](https://www.bolna.ai/docs/post-call/polling-call-status-webhooks)
- [Bolna Hindi voice setup](https://www.bolna.ai/hindi-text-to-speech)
