"""Analyze a STEP file with the Protyus REST API and print what it found.

    export PROTYUS_API_KEY=ak_...     # Preferences > API keys in the app
    export PROTYUS_ORG=org_...        # the organization to act in
    python analyze.py part.step [--process cnc_milling] [--project prj_...]

Standard library only. The API is described at https://app.protyus.ai/api/v1/openapi.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = os.environ.get("PROTYUS_API_URL", "https://app.protyus.ai").rstrip("/")


def call(method: str, path: str, body: dict | None = None) -> dict:
    """One API call, as the person whose key this is, in their organization."""
    key, org = os.environ.get("PROTYUS_API_KEY"), os.environ.get("PROTYUS_ORG")
    if not key or not org:
        sys.exit("Set PROTYUS_API_KEY and PROTYUS_ORG first.")
    request = urllib.request.Request(
        f"{API}{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {key}", "X-Protyus-Org": org, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        sys.exit(f"{method} {path}: {error.code} {error.read().decode(errors='replace')[:300]}")


def upload(step: Path) -> str:
    """Send the file's bytes to a signed upload URL, and return the upload_url an analysis starts from."""
    signed = call("POST", "/api/v1/uploads", {"file_name": step.name})
    if step.stat().st_size > signed["put_url_max_bytes"]:
        sys.exit(f"{step.name} is over {signed['put_url_max_bytes']} bytes: see the upload docs for large files.")
    # The signed URL is its own credential, so this request carries no API key.
    request = urllib.request.Request(signed["put_url"], method="PUT", data=step.read_bytes(),
                                     headers={"Content-Type": "application/octet-stream"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.load(response)["upload_url"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("step", type=Path, help="the STEP file to analyze")
    parser.add_argument("--project", help="the project to put it in (default: your first project)")
    parser.add_argument("--process", help="the process, such as cnc_milling (default: your settings)")
    args = parser.parse_args()

    projects = call("GET", "/api/v1/projects")
    if not args.project and not projects:
        sys.exit("Make a project in the app first, or pass --project.")
    project = args.project or projects[0]["id"]
    body = {"upload_url": upload(args.step), "file_name": args.step.name}
    if args.process:
        body["process"] = args.process
    analysis = call("POST", f"/api/v1/projects/{project}/analyses", body)
    print(f"Analyzing {args.step.name} ({analysis['id']})", end="", flush=True)

    while analysis["status"] not in ("ready", "failed"):
        time.sleep(3)
        print(".", end="", flush=True)
        analysis = call("GET", f"/api/v1/analyses/{analysis['id']}")
    print()
    if analysis["status"] == "failed":
        sys.exit(f"The analysis failed: {analysis.get('error')}")
    report(analysis)


def report(analysis: dict) -> None:
    """The verdict, score, setups, cost and each finding with its fix, on the machine it was planned for."""
    recognition = analysis["result"]["recognition"]
    machine = analysis["machine"]
    dfm = recognition["dfm"].get(machine, {})
    card = dfm.get("scorecard", {})
    score = next((s["value"] for s in card.get("scores", []) if s.get("id") == "general"), None)
    estimate = recognition.get("estimate") or {}
    cost = (estimate.get("cost") or {}).get("each")

    print(f"Machine:  {analysis.get('machine_label') or machine}")
    print(f"Verdict:  {card.get('verdict', {}).get('title', '-')}")
    print(f"DFM score: {score if score is not None else '-'}")
    print(f"Setups:   {len((recognition.get('setup_plan') or {}).get('setups', []))}")
    if cost is not None:
        print(f"Cost each at {estimate.get('quantity', 1)} off: {cost:,.2f}")
    print()
    for finding in dfm.get("findings", []):
        print(f"- {finding['title']}")
        if finding.get("fix"):
            print(f"  Fix: {finding['fix']}")


if __name__ == "__main__":
    main()
