"""HTTP condiviso: contesto TLS e chiamata SPARQL.

Su macOS la catena TLS verso dati.camera.it richiede il truststore di
sistema, non il bundle certifi di default (vedi docs/decisioni.md,
2026-08-05 — "TLS: si usa il truststore di sistema").
"""

import json
import ssl
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

SPARQL_ENDPOINT = "https://dati.camera.it/sparql"

SPARQL_PREFIXES = """
PREFIX ocd:  <http://dati.camera.it/ocd/>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dc:   <http://purl.org/dc/elements/1.1/>
"""

USER_AGENT = "banchi/0 (data journalism)"


def contesto_ssl() -> ssl.SSLContext:
    if sys.platform != "darwin":
        return ssl.create_default_context()
    pem = Path(tempfile.gettempdir()) / "banchi_system_roots.pem"
    if not pem.exists():
        pem.write_text(subprocess.run(
            ["security", "find-certificate", "-a", "-p",
             "/Library/Keychains/System.keychain",
             "/System/Library/Keychains/SystemRootCertificates.keychain"],
            capture_output=True, text=True, check=True).stdout)
    return ssl.create_default_context(cafile=str(pem))


_CTX = contesto_ssl()


def sparql(query: str) -> list[dict]:
    data = urllib.parse.urlencode({"query": SPARQL_PREFIXES + query}).encode()
    req = urllib.request.Request(
        SPARQL_ENDPOINT, data=data,
        headers={"Accept": "application/sparql-results+json",
                 "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300, context=_CTX) as r:
        res = json.loads(r.read().decode())
    return [{k: v["value"] for k, v in b.items()}
            for b in res["results"]["bindings"]]


def scarica(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120, context=_CTX) as r:
        return r.read().decode("utf-8", "replace")
