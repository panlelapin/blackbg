"""Resolve the project classpaths and query OSV for the exact Maven versions."""
import json
from pathlib import Path
import subprocess
import sys
import urllib.request


root = Path(__file__).resolve().parents[1]
output = subprocess.check_output([
    "./gradlew", "--console=plain", "-q", "-I", "tools/dependency-graph.init.gradle",
    "auditDependencyGraph",
], cwd=root, text=True)

failed = False
for scope in ("build", "runtime"):
    prefix = f"AUDIT {scope} "
    coords = sorted({line[len(prefix):] for line in output.splitlines() if line.startswith(prefix)})
    if not coords:
        sys.exit(f"No {scope} dependencies reported; check the Gradle graph.")
    queries = []
    for coord in coords:
        name, version = coord.rsplit(":", 1)
        queries.append({"package": {"ecosystem": "Maven", "name": name}, "version": version})
    request = urllib.request.Request("https://api.osv.dev/v1/querybatch",
                                     data=json.dumps({"queries": queries}).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=90) as response:
        results = json.load(response)["results"]
    if len(results) != len(coords):
        sys.exit("Incomplete OSV response.")
    hits = 0
    for coord, result in zip(coords, results):
        ids = [item["id"] for item in result.get("vulns", [])]
        print(scope, coord, ", ".join(ids) if ids else "OK")
        hits += len(ids)
    print(f"{scope}: {len(coords)} coordinates, {hits} advisory matches")
    failed |= hits != 0
sys.exit(int(failed))
