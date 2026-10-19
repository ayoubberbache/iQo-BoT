"""Optional live knowledge lookups. Streamed in memory (lru_cache, nothing written to disk).
NEVER on the safety-critical path: call from a background thread for 'tell me more' answers."""
import json
import urllib.parse
import urllib.request
from functools import lru_cache

UA = {"User-Agent": "IQO-Bot/1.0"}


def _get(url, timeout=3.0):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return json.loads(r.read().decode())


@lru_cache(maxsize=256)
def pubchem_props(name: str):
    """Formula, molecular weight, CID, CAS-like synonyms (PubChem PUG REST). Returns dict or None."""
    try:
        n = urllib.parse.quote(name)
        p = _get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{n}/property/MolecularFormula,MolecularWeight/JSON")
        return p["PropertyTable"]["Properties"][0]
    except Exception:
        return None


@lru_cache(maxsize=256)
def pubchem_ghs(cid: int):
    """GHS classification text blocks (PUG View). Returns list[str] of H-statements found, or []."""
    try:
        d = _get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON?heading=GHS+Classification")
        out = []
        def walk(x):
            if isinstance(x, dict):
                for v in x.values(): walk(v)
            elif isinstance(x, list):
                for v in x: walk(v)
            elif isinstance(x, str) and x.startswith("H") and x[1:4].isdigit():
                out.append(x)
        walk(d)
        return sorted(set(out))
    except Exception:
        return []


@lru_cache(maxsize=128)
def chembl_search(name: str):
    """ChEMBL molecule search (REST). Returns top hit's id + preferred name or None."""
    try:
        d = _get(f"https://www.ebi.ac.uk/chembl/api/data/molecule/search.json?q={urllib.parse.quote(name)}&limit=1")
        m = d["molecules"][0]
        return {"chembl_id": m["molecule_chembl_id"], "name": m.get("pref_name")}
    except Exception:
        return None

# NOAA CAMEO Chemicals: no public REST API -> Stage 1 rules in guardrail.py encode the reactivity
#   pairs you listed (verify against the CAMEO web 'Chemical Reactivity Worksheet').
# Open Reaction Database: distributed as bulk datasets/web search, no light query API -> not used at runtime.
# Roboflow Universe GHS models: run via Roboflow hosted/inference API with YOUR API key on camera frames
#   (CameraStub in dashboard.py is the hook).
