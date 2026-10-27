# Three-to-five-minute demo

1. Launch the backend and frontend in demo mode; open the **Overview** screen.
   Point out the synthetic-demo notice and database-backed dashboard metrics.
2. Open **Farm Explorer**, choose TX-001, and show the highlighted field
   boundary, coordinate, area, crop, and verification state.
3. Select **Satellite Intelligence**. Explain that this screen uses synthetic
   observations in demo mode, show the NDVI curve, reported date, estimated
   interval, evidence grade, and limitations. Do not describe it as live
   imagery.
4. Open **AI Verification Calls**. Explain the text simulator is a local
   fallback when phone credentials are missing. Choose TX-001 / Cotton / May
   25, 2025 and run it.
5. Show the resulting `WITHIN_TOLERANCE` outcome and state that it is a
   recorded review result—not approval or coverage determination.
6. Run TX-002 with July 4, 2025 and show that the interval gap makes it
   `REVIEW_REQUIRED`; run TX-003 to show `INSUFFICIENT_EVIDENCE`.
7. Open **Claims**, filter by review status, and inspect the corresponding
   evidence for a flagged record.
8. Open **Verification Reports** and use the local PDF link. Highlight the
   algorithm version, evidence provenance, limitations, and human-review
   disclaimer.

For a live extension, configure Bolna as documented in
`VOICE_PROVIDER_SETUP.md`, expose the API over public HTTPS, conduct a real
test call with demo identities, and then show the resulting webhook-driven
Voice Session in the dashboard.
