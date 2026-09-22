"""
R1-D2 §1: GitHub access diagnostic probe.

Auth modes tested (in order), each against a known-public repo:
  A. anonymous  (no Authorization header)
  B. GITHUB_TOKEN env var (if set)
  C. gh auth token (if gh is logged in)

Endpoints probed:
  - repository metadata      GET /repos/{owner}/{repo}
  - list issues              GET /repos/{owner}/{repo}/issues
  - get one issue            GET /repos/{owner}/{repo}/issues/{n}
  - list issue comments      GET /repos/{owner}/{repo}/issues/{n}/comments
  - list issue events        GET /repos/{owner}/{repo}/issues/{n}/events
  - commit lookup            GET /repos/{owner}/{repo}/commits/{sha}
  - pull request lookup      GET /repos/{owner}/{repo}/pulls/{n}

Recorded per (mode, endpoint):
  http_status, error_class, rate_limit_remaining, rate_limit_reset,
  x_accepted_github_permissions, x_oauth_scopes (if present)

422 is classified as VALIDATION_OR_ABUSE_LIMIT unless the response body
explicitly says "permission". Never auto-classify 422 as PERMISSION_DENIED.

Output: results/R1D_ACCESS_DIAGNOSTIC.json
"""
import json, os, ssl, subprocess, urllib.request, urllib.error, time
from pathlib import Path

ROOT = Path("E:/VForge-R0")
RESULTS = ROOT / "r1d" / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# A known-public repo + issue for probing
PROBE_REPO = "google-research/albert"
PROBE_ISSUE = 37          # R1-C CAND-05 referenced issue
PROBE_COMMIT = "d032c58"  # R1-C pre-fix ref (may 404; fine, we record status)
PROBE_PR = 37

def gh_auth_token():
    """Return the token string from `gh auth token`, or None."""
    try:
        r = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=15)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return None

def classify(status, body_text, reason=None):
    """Return (error_class, note). 422 => VALIDATION_OR_ABUSE_LIMIT unless body says permission."""
    if status == 200:
        return "OK", None
    if 200 <= status < 300:
        return "OK", None
    if status == 401:
        return "AUTH_REQUIRED", reason
    if status == 403:
        # Distinguish rate-limit 403 vs permission 403
        if body_text and ("rate limit" in body_text.lower() or "abuse" in body_text.lower()):
            return "RATE_LIMITED", reason
        if body_text and ("permission" in body_text.lower() or "not accessible" in body_text.lower()):
            return "PERMISSION_DENIED", reason
        return "FORBIDDEN", reason
    if status == 404:
        return "NOT_FOUND", reason
    if status == 422:
        # Per protocol: do NOT auto-classify as PERMISSION_DENIED
        if body_text and "permission" in body_text.lower():
            return "PERMISSION_DENIED", "body explicitly states permission"
        return "VALIDATION_OR_ABUSE_LIMIT", "422 default classification"
    if 500 <= status < 600:
        return "SERVER_ERROR", reason
    return f"HTTP_{status}", reason

def http_get(url, token=None, extra_headers=None):
    headers = {"User-Agent": "VForge-R1D2-probe", "Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = "token " + token
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=20, context=ctx)
        status = resp.status
        body = resp.read().decode("utf-8", errors="replace")
        hdrs = {k.lower(): v for k, v in resp.headers.items()}
        return status, body, hdrs
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        hdrs = {k.lower(): v for k, v in e.headers.items()} if e.headers else {}
        return status, body, hdrs
    except Exception as e:
        return 0, str(e), {}

def probe_mode(mode_name, token, extra_header_key=None):
    """Run all 7 endpoints for one auth mode. Return list of result dicts."""
    results = []
    # Build the endpoint list
    endpoints = [
        ("repository_metadata", f"https://api.github.com/repos/{PROBE_REPO}"),
        ("list_issues", f"https://api.github.com/repos/{PROBE_REPO}/issues?per_page=5"),
        ("get_one_issue", f"https://api.github.com/repos/{PROBE_REPO}/issues/1"),
        ("list_issue_comments", f"https://api.github.com/repos/{PROBE_REPO}/issues/1/comments"),
        ("list_issue_events", f"https://api.github.com/repos/{PROBE_REPO}/issues/1/events"),
        ("commit_lookup", f"https://api.github.com/repos/{PROBE_REPO}/commits/master"),
        ("pull_request_lookup", f"https://api.github.com/repos/{PROBE_REPO}/pulls/{PROBE_PR}"),
    ]
    for name, url in endpoints:
        status, body, hdrs = http_get(url, token=token)
        err_class, note = classify(status, body)
        results.append({
            "mode": mode_name,
            "endpoint": name,
            "http_status": status,
            "error_class": err_class,
            "note": note,
            "rate_limit_remaining": hdrs.get("x-ratelimit-remaining"),
            "rate_limit_reset": hdrs.get("x-ratelimit-reset"),
            "x_accepted_github_permissions": hdrs.get("x-accepted-github-permissions"),
            "x_oauth_scopes": hdrs.get("x-oauth-scopes"),
        })
        time.sleep(0.5)
    return results

def main():
    # Determine available auth modes
    gh_tok = gh_auth_token()
    env_tok = os.environ.get("GITHUB_TOKEN")

    all_results = []
    # A. anonymous
    all_results += probe_mode("anonymous", None)
    # B. GITHUB_TOKEN env var
    if env_tok:
        all_results += probe_mode("GITHUB_TOKEN_env", env_tok)
    else:
        all_results.append({"mode": "GITHUB_TOKEN_env", "endpoint": "skipped",
                            "error_class": "NOT_SET", "note": "GITHUB_TOKEN env var not set"})
    # C. gh auth
    if gh_tok:
        all_results += probe_mode("gh_auth", gh_tok)
    else:
        all_results.append({"mode": "gh_auth", "endpoint": "skipped",
                            "error_class": "NOT_AUTHENTICATED",
                            "note": "gh CLI not logged in"})

    # Summarize access level
    # FULL: anonymous can read repo metadata + list issues + get one issue
    # PARTIAL: some read works but comments/events/commits blocked
    # BLOCKED: even basic repo read fails
    anon = [r for r in all_results if r["mode"] == "anonymous"]
    def ok(r, ep): return r.get("endpoint") == ep and r.get("error_class") == "OK"
    base_ok = all(ok(r, ep) for ep in ["repository_metadata", "list_issues", "get_one_issue"]
                  for r in anon if r.get("endpoint") == ep)
    # Simpler: check each of the 3 basic endpoints has an OK anonymous result
    def has_ok(mode, ep):
        return any(r.get("mode") == mode and r.get("endpoint") == ep and r.get("error_class") == "OK" for r in all_results)
    basic_oks = [ep for ep in ["repository_metadata", "list_issues", "get_one_issue"] if has_ok("anonymous", ep)]
    advanced_oks = [ep for ep in ["list_issue_comments", "list_issue_events", "commit_lookup", "pull_request_lookup"]
                    if has_ok("anonymous", ep)]

    if len(basic_oks) == 3 and len(advanced_oks) == 4:
        access_status = "FULL"
    elif len(basic_oks) > 0:
        access_status = "PARTIAL"
    else:
        access_status = "BLOCKED"

    diagnostic = {
        "probe_repo": PROBE_REPO,
        "probe_issue": PROBE_ISSUE,
        "probe_commit": PROBE_COMMIT,
        "probe_pr": PROBE_PR,
        "auth_modes_available": {
            "anonymous": True,
            "GITHUB_TOKEN_env": bool(env_tok),
            "gh_auth": bool(gh_tok),
        },
        "results": all_results,
        "access_status": access_status,
        "note": "No compromised token was used. Only anonymous / GITHUB_TOKEN env / gh auth.",
    }
    out = RESULTS / "R1D_ACCESS_DIAGNOSTIC.json"
    out.write_text(json.dumps(diagnostic, indent=2), encoding="utf-8")
    print(f"Access diagnostic written to {out}")
    print(f"ACCESS_STATUS = {access_status}")
    print(f"  basic_oks   = {basic_oks}")
    print(f"  advanced_oks= {advanced_oks}")
    for r in all_results:
        if r.get("endpoint") != "skipped":
            print(f"  [{r['mode']}] {r['endpoint']:24s} {r['http_status']} {r['error_class']}  rl_rem={r.get('rate_limit_remaining')}")

if __name__ == "__main__":
    main()
