# Security and privacy

Wapsi is a hackathon prototype. It has not had an independent security audit, a legal review or a DPDP Act compliance review.

## What it keeps

- No account and no database. A person's story, dates and results stay in their browser session, on the app server's memory, until the session ends or they click Delete my session data.
- Evidence files are read once to compute a SHA-256 fingerprint. The file and its name are not kept.
- The hash-chained log holds events and fingerprints, never the story.

## What leaves the app

| Destination | What is sent | When |
|---|---|---|
| LLM provider | The story, after secrets are blocked and identifiers masked, plus the dates and amounts entered | Only after the consent box is ticked |
| ifsc.razorpay.com | The IFSC entered | When someone enters one |
| RBI and portal sites | Nothing personal, only page requests | Live source checks |

## Threats and controls

| Threat | Control | Known limit |
|---|---|---|
| A victim pastes an OTP or PIN | Blocked in code before storage, in English, Hindi and Telugu | A bare number with no label gets through |
| Identifiers reach the LLM | PAN, Aadhaar, card and account patterns are masked | Numbers written in words are not masked |
| Prompt injection in pasted text | Text is wrapped as data, output is schema-checked, and deadlines come from plain code | The model could still word a draft badly, so the person must check it |
| The AI invents a number or promises money | The fact checker rejects the draft | It checks numbers and promise phrases, not every claim |
| Script injection | User text is never passed to raw HTML | Depends on keeping that rule |
| Abuse of the AI key | Call limit per session | A new session resets it; needs a hosted rate limiter |
| Hammering government sites | Results cached for 5 minutes | Cache is per server |
| Leaked secrets | Secrets stay in environment variables, and CI scans the repo | Rotate a key if one is ever exposed |
| Vulnerable dependencies | Versions pinned, and pip-audit runs in CI | Only finds known issues |
| A false complaint | Wapsi never accepts the declaration, logs in or submits | The person is responsible for what they file |

## Not built yet

Hosted database with encryption and retention, hosted rate limiting, monitoring and alerting, custom security headers on Streamlit's hosting, an independent security audit, and a DPDP Act compliance review.

## Reporting a problem

Open an issue on the GitHub repository without including any personal data or exploit details, and ask for a private contact.
