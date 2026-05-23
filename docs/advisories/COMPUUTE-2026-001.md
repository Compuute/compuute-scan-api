# COMPUUTE-2026-001 — Argument injection via `npx` in trycua/cua MCP server runtime

| Field | Value |
|-------|-------|
| **Advisory ID** | COMPUUTE-2026-001 |
| **Status** | **PRE-DISCLOSURE — DO NOT DISTRIBUTE** |
| **Discovery** | 2026-05-22 (Compuute self-batch scan of 19 production MCP repos) |
| **Reporter** | Daniel Abbay — daniel@compuute.se |
| **Vendor** | trycua / Cua Inc. — https://github.com/trycua/cua |
| **Affected** | `libs/cuabot/src/client.ts` at HEAD as of 2026-05-22 (commit pending verification with vendor) |
| **Detector rule** | `compuute-scan` L1-038 (CWE-88, OWASP A03:2021, CAPEC-88) |
| **Severity (proposed)** | **High** — depends on whether `currentSessionName` can be set from MCP protocol input |
| **CVSS v4 (proposed)** | AV:N/AC:L/AT:N/PR:L/UI:N/VC:H/VI:H/VA:N — 8.5 if confirmed exploitable |
| **Disclosure timeline** | 90-day coordinated disclosure starting 2026-05-23 |
| **Public-by** | 2026-08-21 (or earlier if vendor confirms fix is live and reporter agrees) |

## Summary

The MCP server in `trycua/cua` spawns the `npx` binary with arguments that include an externally-settable variable (`currentSessionName`). Because `npx` interprets its own flags before delegating to the named package, an attacker who controls `currentSessionName` can inject runner-level flags such as `--package=@evil/pkg` or `-c "evil code"`, bypassing any allowlist applied at the package-name level.

This pattern is the same class as the Ox Security "npx argument injection" research published earlier this month.

## Affected code (verbatim, from public source)

`libs/cuabot/src/client.ts:21-234`:

```typescript
let currentSessionName: string | null = null;

// (setter — accepts external input)
export function setSessionName(name: string): void {
  currentSessionName = name;
}

// (consumer — passed unsanitized to npx)
const spawnArgs = ['cuabot', '--serve'];
if (currentSessionName) {
  spawnArgs.push('--name', currentSessionName);
}
const child = spawn('npx', spawnArgs, {
  detached: true,
  stdio: ['ignore', 'ignore', logFd],
  cwd: process.cwd(),
  windowsHide: true,
  shell: process.platform === 'win32',  // <-- on Windows this also enables shell metacharacter expansion
});
```

## Threat model

| Step | Required attacker capability |
|------|------------------------------|
| 1 | Control the input that reaches `setSessionName` |
| 2 | Set value to `--package=@evil/pkg --` or `--call='require("child_process").execSync(...)'` |
| 3 | (On Windows only) shell-expand the args because `shell: process.platform === 'win32'` |
| 4 | Code execution on the host running cuabot |

Whether step 1 is reachable through the MCP protocol (e.g. via a tool-description field or session-id passed by the orchestrator) is the **single remaining question** before this is confirmed exploitable. That investigation is the next disclosure step.

## What compuute-scan detected

Rule L1-038 ("MCP runner-binary argument injection") fired on the `spawn('npx', spawnArgs, …)` call. The disclaimer in the response correctly stated that exploitability requires manual dataflow review — which is what this advisory provides.

## Suggested mitigation

1. Pin the runner-binary call: `npx --package=@trycua/cuabot@<exact-version> -- --serve` and place the session name after `--` so npx never interprets it as a flag.
2. Validate `currentSessionName` against a strict regex (`^[A-Za-z0-9_-]{1,32}$`) before passing it to `spawn`.
3. Set `shell: false` unconditionally; the Windows fallback to shell-mode is a foot-gun.
4. Consider replacing the package-runner call with a direct binary spawn once the cuabot package is installed.

## Coordinated disclosure timeline

- **2026-05-23 (day 0)** — Discovery in public source; this draft created.
- **Day 0–3** — Email vendor at security@trycua.com (or equivalent) with this advisory + reproducer. Pre-fill GPG-encrypted if vendor publishes a key.
- **Day 3–60** — Vendor coordinates fix; reporter available for technical questions.
- **Day 60–90** — Coordination on public advisory wording; CVE request via MITRE if vendor concurs.
- **Day 90 (2026-08-21)** — Public advisory published at https://compuute.se/security/COMPUUTE-2026-001 unless earlier release agreed.

## Vendor coordination log

| Date | Action | Status |
|------|--------|--------|
| 2026-05-23 | Draft created from compuute-scan L1-038 finding | done |
| 2026-05-23 | Vendor email sent to security@trycua.com | **pending — Daniel action** |

## What you can do now if you operate cuabot

This advisory is pre-disclosure. The mitigation steps above are publicly safe and recommended for any operator concerned about runner-binary argument injection in MCP servers built around `npx`. The same risk class applies to any MCP server that spawns `npx`/`uvx`/`pipx`/`pnpx` with arguments derived from external input — run `compuute-scan` against your own MCP servers to detect the pattern in your codebase.

## Public advisory release plan

Upon publication (day 90 or earlier with vendor agreement):

- Publish at https://compuute.se/security/COMPUUTE-2026-001
- Submit CVE-request to MITRE
- Coordinate vendor advisory release (if vendor publishes one)
- Reference in compuute-scan CHANGELOG as the first advisory under the Compuute name
- LinkedIn post + Show HN coordinated with disclosure date

---

**This advisory file is pre-disclosure. Do not commit it to a public branch until day 90 OR vendor has confirmed publication is appropriate. If you're reading this in a public branch, it means disclosure has completed.**
