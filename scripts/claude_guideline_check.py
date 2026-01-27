#!/usr/bin/env python
"""
Claude guideline checker for pre-commit.

- Reads CLAUDE.md and .claude/*.md instruction files.
- Gets the staged diff and filenames.
- Lists available Anthropic models FIRST and selects a valid model.
- Sends a compact prompt to Claude (Anthropic API) to verify alignment.
- Exits non-zero to block commit if violations are found.

Security & SOC2 notes:
- Only staged diff + relevant instruction excerpts are sent.
- Redacts obvious secrets and large blobs before sending.
- Fails closed (blocks commit) on API/network errors to avoid bypassing review.

Exit codes:
  0 = pass / skipped
  1 = violations found (commit blocked)
  2 = configuration/runtime error (fail closed)
"""

import os
import sys
import json
import subprocess
import glob
import re
import time
import textwrap
from pathlib import Path
from typing import List, Dict, Any

# ---- Configuration ----
MAX_INSTRUCTION_CHARS = 35_000    # safety bound to keep prompt within model limits
MAX_DIFF_CHARS = 20_000           # keep requests small for latency/cost control
REQUIRED_FILES = ["CLAUDE.md"]    # hard requirement
OPTIONAL_DIR = ".claude"          # read all *.md here

# Preferred models (first hit wins). You can override via env CLAUDE_MODEL.
PREFERRED_MODELS = [
    "claude-3-7-sonnet-latest",
    "claude-3-7-sonnet-20250219",
    "claude-3-5-sonnet-latest",
]

# Patterns to redact secrets in diff (add org-specific as needed)
SECRET_PATTERNS = [
    r"(?i)(aws_)?secret(_access)?_key\s*=\s*['\"][^'\"\n]+['\"]",
    r"(?i)access_key_id\s*=\s*['\"][^'\"\n]+['\"]",
    r"(?i)api_?key\s*[:=]\s*['\"][^'\"\n]+['\"]",
    r"(?i)authorization:\s*bearer\s+[A-Za-z0-9\-_\.=]+",
    r"(?i)password\s*[:=]\s*['\"][^'\"\n]+['\"]",
    r"(?i)token\s*[:=]\s*['\"][^'\"\n]+['\"]",
    r"(?i)client_secret\s*[:=]\s*['\"][^'\"\n]+['\"]",
    r"(?i)-----BEGIN [A-Z ]+ PRIVATE KEY-----.*?-----END [A-Z ]+ PRIVATE KEY-----",
]

# Limit extremely large, likely-generated or vendored hunks
BINARY_FILENAME_HINTS = (".min.", ".map", ".lock", "package-lock.json", "pnpm-lock.yaml", "poetry.lock")


def run(cmd: List[str]) -> str:
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{res.stderr}")
    return res.stdout


def get_staged_filenames() -> List[str]:
    out = run(["git", "diff", "--cached", "--name-only"])
    files = [line.strip() for line in out.splitlines() if line.strip()]
    return files


def get_staged_diff() -> str:
    diff = run(["git", "diff", "--cached"])
    return diff


def read_instructions() -> str:
    buf = []
    root = Path(".")
    # Required file(s)
    for f in REQUIRED_FILES:
        p = root / f
        if not p.exists():
            print(f"[claude-check] Missing required instruction file: {f}", file=sys.stderr)
            sys.exit(2)
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            buf.append(f"# FILE: {f}\n{text}\n")
        except Exception as e:
            print(f"[claude-check] Failed to read {f}: {e}", file=sys.stderr)
            sys.exit(2)
    # Optional .claude/*.md
    for p in sorted(glob.glob(f"{OPTIONAL_DIR}/**/*.md", recursive=True)):
        try:
            text = Path(p).read_text(encoding="utf-8", errors="replace")
            buf.append(f"# FILE: {p}\n{text}\n")
        except Exception:
            pass
    merged = "\n\n".join(buf)
    if len(merged) > MAX_INSTRUCTION_CHARS:
        merged = merged[:MAX_INSTRUCTION_CHARS] + "\n\n...[truncated instructions]..."
    return merged


def looks_like_binary_path(path: str) -> bool:
    return any(h in path for h in BINARY_FILENAME_HINTS)


def redact(text: str) -> str:
    redacted = text
    for pat in SECRET_PATTERNS:
        redacted = re.sub(pat, "[REDACTED]", redacted, flags=re.DOTALL)
    # Trim very long file hunks (binary or vendored artifacts)
    if len(redacted) > MAX_DIFF_CHARS:
        redacted = redacted[:MAX_DIFF_CHARS] + "\n...[truncated diff]..."
    return redacted


def build_prompt(instructions: str, filenames: List[str], diff: str) -> str:
    files_str = "\n".join(filenames) if filenames else "(no files)"
    return f"""
You are a strict senior Django reviewer. Validate that the staged changes comply with our engineering rules and security/SOC2 guidance defined in these instruction docs.

=== INSTRUCTIONS (from CLAUDE.md and .claude/*.md) ===
{instructions}

=== STAGED FILES ===
{files_str}

=== STAGED DIFF (git diff --cached) ===
{diff}

Return ONLY a compact JSON object with this schema:
{{
  "verdict": "pass" | "fail",
  "summary": "<one-paragraph summary>",
  "violations": [
    {{
      "title": "<short rule name>",
      "severity": "high|medium|low",
      "instruction_ref": "<file#section if possible>",
      "details": "<what violated and why>",
      "suggestion": "<minimal fix>"
    }}
  ]
}}
If compliant, set "violations" to [].
""".strip()


def resolve_model(client) -> str:
    """
    Determine a valid Anthropic model to use:
      1) If CLAUDE_MODEL env is set and available, use it.
      2) Try PREFERRED_MODELS in order.
      3) Fallback: first model that startswith('claude-3-7-sonnet-') or ('claude-3-5-sonnet-').
      4) As a last resort, pick the first model returned.
    """
    try:
        resp = client.models.list()
        available = [m.id for m in resp.data]
    except Exception as e:
        print(f"[claude-check] Failed to list Anthropic models: {e}", file=sys.stderr)
        sys.exit(2)

    if not available:
        print("[claude-check] No Anthropic models available from API.", file=sys.stderr)
        sys.exit(2)

    print(f"[claude-check] Available models: {available}", file=sys.stderr)

    env_model = os.getenv("CLAUDE_MODEL")
    if env_model:
        if env_model in available:
            print(f"[claude-check] Using env model: {env_model}", file=sys.stderr)
            return env_model
        else:
            print(f"[claude-check] Env model '{env_model}' not available; will try fallbacks.", file=sys.stderr)

    for m in PREFERRED_MODELS:
        if m in available:
            print(f"[claude-check] Using preferred model: {m}", file=sys.stderr)
            return m

    for prefix in ("claude-3-7-sonnet-", "claude-3-5-sonnet-"):
        for m in available:
            if m.startswith(prefix):
                print(f"[claude-check] Using heuristic fallback model: {m}", file=sys.stderr)
                return m

    chosen = available[0]
    print(f"[claude-check] Using last-resort model: {chosen}", file=sys.stderr)
    return chosen


def _strip_to_json_blob(s: str) -> str:
    """
    Best-effort: remove surrounding code fences and extract the first {...} JSON object.
    """
    if not s:
        return s
    s = s.strip()
    # Remove ```json ... ``` or ``` ... ```
    if s.startswith("```"):
        # strip leading/backtick fences conservatively
        s = s.strip("`").lstrip("json").strip()
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        return s[start:end+1]
    return s


def parse_bot_json(text: str) -> Dict[str, Any]:
    """
    Parse and minimally validate the JSON schema we expect from Claude.
    Saves raw output to /tmp/claude_check_last.txt for debugging.
    Fail closed if parsing fails.
    """
    raw = text or ""
    try:
        Path("/tmp").mkdir(parents=True, exist_ok=True)
        (Path("/tmp") / "claude_check_last.txt").write_text(raw, encoding="utf-8")
    except Exception:
        pass

    cleaned = _strip_to_json_blob(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("[claude-check] Could not parse Claude JSON. Saved raw to /tmp/claude_check_last.txt", file=sys.stderr)
        print(f"[claude-check] JSON error: {e}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(data, dict):
        print("[claude-check] Claude output is not a JSON object.", file=sys.stderr)
        sys.exit(2)

    if "verdict" not in data or data["verdict"] not in ("pass", "fail"):
        print("[claude-check] Missing or invalid 'verdict' field in Claude JSON.", file=sys.stderr)
        sys.exit(2)

    if "violations" in data and not isinstance(data["violations"], list):
        print("[claude-check] 'violations' must be a list.", file=sys.stderr)
        sys.exit(2)

    data.setdefault("summary", "")
    data.setdefault("violations", [])
    return data


def call_claude(prompt: str, client, model: str) -> Dict[str, Any]:
    """
    Invoke Anthropic Messages API requesting strict JSON.
    - Tries response_format when supported by SDK.
    - Falls back to prompt-only JSON enforcement on older SDKs.
    - Retries once with a shorter minimal prompt if parsing fails.
    """
    from anthropic import APIStatusError
    import textwrap, time

    def _ask_with_json(p: str) -> str:
        # Try modern SDK with response_format
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=2000,
                temperature=0,
                response_format={"type": "json_object"},  # may raise TypeError on old SDKs
                system="Return strict JSON only. No prose. No markdown. No code fences.",
                messages=[{"role": "user", "content": p}],
            )
            return "".join(getattr(b, "text", "") for b in msg.content)
        except TypeError:
            # Old SDK path: no response_format; enforce via prompt
            msg = client.messages.create(
                model=model,
                max_tokens=2000,
                temperature=0,
                system=(
                    "You MUST output strict JSON only (no prose, no code fences). "
                    "Schema: {verdict:'pass'|'fail', summary:str, violations:[{title,severity, instruction_ref, details, suggestion}]}. "
                    "If unsure, set verdict='fail'."
                ),
                messages=[{"role": "user", "content": p}],
            )
            return "".join(getattr(b, "text", "") for b in msg.content)

    # Diagnostics
    print(f"[claude-check] Prompt size: {len(prompt)} chars", file=sys.stderr)

    try:
        raw = _ask_with_json(prompt)
        try:
            return parse_bot_json(raw)
        except SystemExit:
            # Retry once with a minimal prompt (cap length to reduce odd outputs)
            minimal = textwrap.dedent("""\
            Output ONLY strict JSON with keys: verdict('pass'|'fail'), summary, violations(list of {title,severity,instruction_ref,details,suggestion}).
            If unsure, set verdict='fail'.
            """)
            time.sleep(0.35)
            raw2 = _ask_with_json(minimal + "\n\n" + prompt[:12000])
            return parse_bot_json(raw2)

    except APIStatusError as e:
        print(f"[claude-check] Anthropic API error for model '{model}': {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"[claude-check] Unexpected Anthropic client error: {e}", file=sys.stderr)
        sys.exit(2)


def main():
    filenames = get_staged_filenames()
    if not filenames:
        print("[claude-check] No staged files. Skipping.", file=sys.stderr)
        sys.exit(0)

    # Optionally skip obviously large/noisy files (still list them in prompt)
    interesting = [f for f in filenames if not looks_like_binary_path(f)]

    instructions = read_instructions()
    diff_raw = get_staged_diff()
    diff = redact(diff_raw)

    # Size diagnostics (helps detect context bloat)
    print(
        f"[claude-check] Instructions size: {len(instructions)} chars; Diff size (redacted): {len(diff)} chars",
        file=sys.stderr,
    )

    prompt = build_prompt(instructions, interesting or filenames, diff)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[claude-check] ANTHROPIC_API_KEY not set. Failing closed.", file=sys.stderr)
        sys.exit(2)

    try:
        from anthropic import Anthropic
    except Exception as e:
        print(f"[claude-check] Anthropic SDK not installed: {e}\nRun: pip install anthropic", file=sys.stderr)
        sys.exit(2)

    client = Anthropic(api_key=api_key)
    model = resolve_model(client)
    result = call_claude(prompt, client, model)

    verdict = result.get("verdict", "fail").lower()
    summary = result.get("summary", "")
    violations = result.get("violations", [])

    print("\n[Claude Guideline Check]")
    print(summary or "(no summary)")

    if violations:
        print("\nViolations:")
        for v in violations:
            title = v.get("title", "")
            sev = v.get("severity", "")
            ref = v.get("instruction_ref", "")
            details = v.get("details", "")
            fix = v.get("suggestion", "")
            print(f"- [{sev}] {title}")
            if ref:
                print(f"  ref: {ref}")
            if details:
                print(f"  details: {details}")
            if fix:
                print(f"  fix: {fix}")
    print()

    if verdict != "pass" or violations:
        print("[claude-check] Commit blocked. Address the issues or SKIP if appropriate.", file=sys.stderr)
        sys.exit(1)

    print("[claude-check] Passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
