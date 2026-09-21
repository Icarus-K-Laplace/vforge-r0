"""Fetch W&B run data for public projects via GraphQL API."""
import urllib.request, ssl, json, time, sys

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def gql(entity, project, extra="state", timeout=45):
    node_fields = "name displayName " + extra
    q = ('{ entity(name: "' + entity + '") { project(name: "' + project + '") { '
         'runs(first: 200) { edges { node { ' + node_fields + ' } } } } } }')
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
        ("gregor99", "view_batch_model", "external/viewbatchmodel_wandb.json"),
        ("confusezius", "RevisitDML", "external/revisitdml_wandb.json"),
    ]:
        print(f"Fetching {ent}/{proj} (state+summaryMetrics only)...")
        data = gql(ent, proj, extra="state summaryMetrics")
        if data and data.get("data") and data["data"].get("entity"):
            ed = data["data"]["entity"]["project"]["runs"]["edges"]
            print(f"  Got {len(ed)} runs")
            with open(out, "w") as f:
                json.dump(ed, f)
            # show sample
            for e in ed[:3]:
                node = e.get("node", {})
                print(f"  {node.get('displayName')}: state={node.get('state')}")
        else:
            print("  No data returned")
        time.sleep(8)
