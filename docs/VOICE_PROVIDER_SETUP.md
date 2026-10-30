# Bolna Voice Provider Setup

## Status in this repository

The Bolna provider adapter, generic provider interface, webhook normalization,
idempotency constraints, and local text simulation are implemented. No live
phone call was made from this repository: no Bolna account credentials or
telephone configuration were supplied.

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
