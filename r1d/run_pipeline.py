"""
R1-D2 §2-§4 one-shot runner: waits for anonymous core rate-limit to reset,
then executes paginate -> expand_evidence -> adjudicate in sequence.
No token. Anonymous public REST only. 422 stays VALIDATION_OR_ABUSE_LIMIT.
"""
import ssl, time, urllib.request, json, subprocess, sys
from pathlib import Path

ROOT = Path("E:/VForge-R0")
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

def remaining():
    try:
        req = urllib.request.Request("https://api.github.com/rate_limit", headers={"User-Agent":"vforge-r1d2"})
        d = json.loads(urllib.request.urlopen(req, timeout=15, context=ctx).read())
        return int(d["resources"]["core"]["remaining"]), int(d["resources"]["core"]["reset"])
    except Exception as e:
        print(f"rate_limit check failed: {e}")
        return 0, int(time.time())

def wait_for_quota(need=30, max_wait=1800):
    print(f"Waiting for anonymous core quota >= {need}...")
    deadline = time.time() + max_wait
    while time.time() < deadline:
        rem, _ = remaining()
        if rem >= need:
            print(f"  quota ready: {rem} remaining")
            return True
        print(f"  quota={rem} (need {need}); sleeping 60s")
        time.sleep(60)
    print("  max wait reached, proceeding anyway (requests will 403)")
    return False

def run(script):
    print(f"\n=== running {script} ===")
    r = subprocess.run([sys.executable, str(ROOT/"r1d"/script)], cwd=str(ROOT), capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        print(f"  {script} exited {r.returncode}")
    return r.returncode

def main():
    # Ensure the leads pool exists; if not, re-run pagination first.
    need = 25
    if wait_for_quota(need):
        pass
    run("paginate_issues.py")
    time.sleep(2)
    run("expand_evidence.py")
    time.sleep(2)
    rc = run("adjudicate_leads.py")
    print(f"\n=== R1-D2 §2-§4 pipeline exit code: {rc} ===")

if __name__ == "__main__":
    main()
