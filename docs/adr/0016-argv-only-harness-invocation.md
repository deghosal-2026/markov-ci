# ADR-0016: Harness invocation is argv-only — the prompt is never a shell string

**Status:** Accepted
**Date:** 2026-11-17

## Context

The v0.1.1 review (FIX-01, Critical) found the harness adapter ran `command_template`
through a shell (`shell=True`), substituting `%PROMPT%` into the command string with
ad-hoc `"` escaping. Any shell metacharacter in the prompt — `$(…)`, backticks, `;`,
`|`, `&&`, newlines, `$HOME`, quotes — executed on the host. The prompt carries
attacker-influenceable input (triage output, PR context), so this was remote code
execution through the prompt.

The earlier allowance for shell composition (attributed to ADR-0007) assumed a *trusted*
template. Because `%PROMPT%` is an untrusted **argument** inside that template, the
assumption was wrong.

## Decision

Harness invocation is **argv-only**:

1. Split `command_template` with `shlex.split` **before** substituting `%PROMPT%`.
2. Substitute the prompt as **one argv element**.
3. Run `subprocess.run(argv, shell=False)`.
4. Remove the ad-hoc `"` escaping.
5. Reject templates that re-enter a shell with the prompt (`argv[0]` in
   `{sh, bash, zsh, dash, pwsh, powershell, cmd}` when `%PROMPT%` follows `-c` / `/c`);
   the safe positional form (`bash -c 'tool "$1"' _ %PROMPT%`) stays allowed.
6. Validate templates at config load (empty, unbalanced quotes, missing `%PROMPT%`,
   `%PROMPT%` as the program name) — invalid config, exit **4**.
7. Offer `%PROMPT_FILE%` (a `0600` temp file) or stdin so long prompts stay off
   `ps` / ARG_MAX.

This **supersedes the shell-composition allowance** previously attributed to ADR-0007.
ADR-0007's core decision — target harness CLIs, not raw model SDKs — stands.

## Considered options

- **argv-only (chosen).** No shell parses the prompt; injection is designed out.
- **Keep the shell and "escape the prompt".** Rejected: safe shell escaping is a
  famously endless game, and it keeps a shell in the path for no benefit.
- **Typed template object (per-harness arg arrays).** Cleaner than a string template, but
  a larger config change; revisit if templates ever need structure beyond argv.

## Consequences

- The prompt is inert: metacharacters reach the child verbatim, and nothing parses them.
- Templates lose shell composition (pipes, globs); a team needing composition writes a
  wrapper script, which is then *their* boundary to own.
- `%PROMPT%` stays visible in `ps` / ARG_MAX until `%PROMPT_FILE%` is used — documented,
  not hidden.
- **Falsifier:** any path by which the prompt reaches a shell is a security-class bug —
  fix it, add a regression test, record it.
