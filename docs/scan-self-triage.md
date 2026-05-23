# Scan-self triage

When `compuute-scan-api` is scanned by itself, it produces a small number of findings that are useful test cases for both the scanner and the framing-honesty principle.

This document records the live triage so anyone running `curl https://scan.compuute.se/v1/scan -d '{"repo_url":"https://github.com/Compuute/compuute-scan-api"}'` can compare their output to our analysis.

## Pre-fix baseline (issue #2 opening state)

| Finding | Rule | File:Line | Verdict |
|---------|------|-----------|---------|
| `L1-017` CORS wildcard | high | `main.py:61` | **True positive** — fixed in commit `4b0c318` |
| `L1-009` Dynamic import | high | `api/routes/scan_x402.py:15` | **False positive** — multi-line `from X import (a, b)` matched as if dynamic |
| `L1-009` Dynamic import | high | `tests/test_scan.py:13` | **False positive** — same pattern |
| `L1-009` Dynamic import | high | `tests/test_x402.py:93` | **False positive** — same pattern |
| `L1-011` Security headers missing | medium | `(entire codebase)` | **Accepted** — Railway terminates HTTPS upstream; HSTS is set there; we may add a SecurityHeadersMiddleware later |

## Why we keep the L1-009 false positives unsuppressed

We do not silence the scanner on its own output. The L1-009 multi-line-import FP class is a real upstream bug in `compuute-scan` and should be fixed there with the same honest framing as L1-038. Suppressing locally would hide a real precision issue from other consumers of the scanner.

Tracked upstream: TODO open issue at `Compuute/compuute-scan` once a reproducer test case is added.

## Post-fix expected score

After commit `4b0c318` lands on the live deployment:

```bash
curl -s -X POST https://scan.compuute.se/v1/scan \
  -H 'Content-Type: application/json' \
  -d '{"repo_url":"https://github.com/Compuute/compuute-scan-api"}' \
  | jq '{score, summary}'
```

Expected:

```
{
  "score": 73 or higher,
  "summary": {
    "critical": 0,
    "high": 3,
    "medium": 1,
    "low": 0,
    "info": 0,
    "files_scanned": 17
  }
}
```

The remaining 3 high findings are the L1-009 FPs documented above. The 1 medium is the `L1-011` whole-codebase security-headers check, accepted with rationale.

Score formula (from `api/services/scan.py::_compute_score`):

```
penalty = 25*critical + 8*high + 3*medium + 1*low
score   = max(0, 100 - penalty)
        = max(0, 100 - (0*25 + 3*8 + 1*3))
        = max(0, 100 - 27)
        = 73
```

## Why this matters

A scanner that scores its own producer at 0 (because of its own regex patterns matching internal source) erodes trust on the first 30-second demo. We documented the issue openly, triaged each finding, fixed the one real issue, and explained the remaining false positives. That posture is the product, not embarrassment.
