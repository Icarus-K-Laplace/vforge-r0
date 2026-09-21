"""Fetch DiffSynth W&B project runs (public)."""
import urllib.request, ssl, json, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def gql(entity, project, extra="state", timeout=45):
    node_fields = "name displayName " + extra
    q = ('{ entity(name: "' + entity + '") { project(name: "' + project + '") { '
         'runs(first: 300) { edges { node { ' + node_fields + ' } } } } } }')
    payload = json.dumps({"query": q}).encode()
    req = urllib.request.Request(
        "https://api.wandb.ai/graphql",
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    )
    for a in range(4):
        try:
            r = urllib.request.urlopen(req, timeout=timeout, context=ctx)
            return json.loads(r.read().decode("utf-8", "ignore"))
        except Exception as e:
            if "SSL" in str(e):
                time.sleep(8 * (a + 1))
            else:
                print(f"  ERR {entity}/{project}: {type(e).__name__}: {str(e)[:120]}")
                return None
    return None

if __name__ == "__main__":
    for ent, proj, out in [
        ("tlips", "dsd-mugs-cvpr", "stage1b/external/diffsynth_wandb_mugs.json"),
        ("tlips", "dsd-shoes-cvpr", "stage1b/external/diffsynth_wandb_shoes.json"),
        ("tlips", "dsd-tshirts-cvpr", "stage1b/external/diffsynth_wandb_tshirts.json"),
    ]:
        print(f"Fetching {ent}/{proj} ...")
        data = gql(ent, proj, extra="state summaryMetrics config")
        if data and data.get("data") and data["data"].get("entity"):
            ed = data["data"]["entity"]["project"]["runs"]["edges"]
            print(f"  Got {len(ed)} runs -> {out}")
            with open(out, "w") as f:
                json.dump(ed, f)
            for e in ed[:3]:
                n = e.get("node", {})
                print(f"    {n.get('displayName')}: state={n.get('state')}")
        else:
            print("  No data returned (project not public?)")
        time.sleep(6)
