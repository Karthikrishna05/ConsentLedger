"""ConsentLedger demo server: what an Account Aggregator policy says, checked and fingerprinted on Sepolia.

    python app.py                 # http://127.0.0.1:7860: frontend at /, JSON API at /api (/api/docs), Gradio at /gradio
    python app.py --gradio-only   # the Gradio page alone (supports --share and DEMO_PASSWORD)
    python app.py --selfcheck     # check the routes without loading any model

Both pages use the same input checks and `pipeline.end_to_end.run()` as the experiments, so they cannot drift.
Research use only (NER trained on non-commercial OPP-115). Optional .env: SEPOLIA_RPC_URL, SEPOLIA_PRIVATE_KEY.
"""
from __future__ import annotations

import html
import json
import os
import sys
import tempfile
import threading
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import gradio as gr  # noqa: E402

from consentledger.chain import web3_client  # noqa: E402,F401  (loads .env)
from consentledger.pipeline.end_to_end import load_models, read_document, run, summary_line  # noqa: E402

MAX_CHARS = 300_000                 # a long T&C is ~60k characters
MAX_FILE_MB = 10
MAX_CHAIN_WRITES = 20               # ponytail: per-process cap on test-ETH spend; a per-user limit if it goes public
CAN_READ = bool(os.environ.get("SEPOLIA_RPC_URL"))
CAN_WRITE = CAN_READ and bool(os.environ.get("SEPOLIA_PRIVATE_KEY"))
FRONTEND = ROOT / "frontend"
LABELS = {"DATA_TYPE": "Your data", "PURPOSE": "Purpose", "THIRD_PARTY": "Shared with"}
COLORS = {"Your data": "#b9d7ff", "Purpose": "#c8f0c8", "Shared with": "#ffd9a8", "Promised NOT done": "#f4b6b6"}
DEMO_CONSENT = (ROOT / "data" / "aa" / "consent_artefacts" / "demo_consent.json").read_text(encoding="utf-8")
EXAMPLE_POLICY = """1. INFORMATION WE COLLECT
We collect your bank statements, PAN and mobile number when you register on the Platform, and we use them to assess your eligibility for a loan.
2. SHARING
We share your financial information with credit bureaus and lenders only with your explicit consent. We shall not access your user authentication credentials. We will not sell your mobile number to advertisers.
3. RETENTION
We keep your data only as long as the consent you gave allows, and you may revoke your consent at any time."""

MODELS = None
_lock, _writes = threading.Lock(), 0
_run_lock = threading.Lock()        # one analysis at a time on the GPU, whichever page asked


def _models():
    global MODELS
    with _lock:
        if MODELS is None:
            MODELS = load_models()
    return MODELS


# ------------------------------------------------------------------ shared by both pages
def _analyse_core(text: str, consent_text: str, record: bool) -> tuple[str, dict]:
    """Validate the inputs and run the pipeline. Raises ValueError with a message for the user."""
    global _writes
    text = (text or "").strip()
    if not text:
        raise ValueError("Paste a policy or upload a .txt, .html or .pdf file.")
    if len(text) > MAX_CHARS:
        raise ValueError(f"That document is {len(text):,} characters; the limit is {MAX_CHARS:,}.")
    artefact = None
    if (consent_text or "").strip():
        try:
            artefact = json.loads(consent_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"The consent artefact is not valid JSON: {e}")
        if not isinstance(artefact, dict):
            raise ValueError("The consent artefact must be a JSON object.")
    if record and not artefact:
        raise ValueError("Recording on-chain needs the consent artefact: its expiry is what the chain enforces.")
    if record:
        with _lock:
            if not CAN_WRITE or _writes >= MAX_CHAIN_WRITES:
                raise ValueError("Recording on-chain is not available on this server right now.")
            _writes += 1
    with _run_lock:
        return text, run(text, artefact, _models(), chain=bool(record))   # ValueError, e.g. an expired consent


def _check_core(consent_id: str, record) -> dict:
    if not CAN_READ:
        raise ValueError("Checking needs SEPOLIA_RPC_URL in the server's settings.")
    if not (consent_id or "").strip() or not isinstance(record, dict):
        raise ValueError("Give the consent id and the report it came from.")
    from consentledger.chain.read_consent import check
    try:
        return check(consent_id.strip(), record)
    except (ValueError, KeyError) as e:
        raise ValueError(f"Could not check: {e}")


def _save_report(r: dict) -> Path:
    out = Path(tempfile.mkdtemp()) / "consentledger_report.json"
    out.write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
    return out


# ------------------------------------------------------------------ the Gradio page (backup)
def _highlights(text: str, facts: list[dict]) -> list[tuple[str, str | None]]:
    out, pos = [], 0
    for f in sorted(facts, key=lambda f: f["start"]):
        if f["start"] < pos:
            continue
        out += [(text[pos:f["start"]], None), (text[f["start"]:f["end"]], "Promised NOT done" if f["denied"] else LABELS[f["label"]])]
        pos = f["end"]
    return out + [(text[pos:], None)]


def _fact_list(facts: list[dict]) -> str:
    items = "".join(f"<li><b>{html.escape(f['text'])}</b> &middot; {LABELS[f['label']].lower()}"
                    + (" &middot; <span style='color:#b00020'>the policy says this is NOT done</span>" if f["denied"] else "")
                    + "</li>" for f in facts)
    return f"<ul>{items}</ul>" if items else ""


def _passages_html(text: str, r: dict) -> str:
    badge = {"show": ("#1f8a4c", "summary checked"), "add": ("#c26a00", "summary checked - some facts added"),
             "reject": ("#b00020", "summary failed the check - showing the facts instead")}
    cards = []
    for i, p in enumerate(r["passages"], 1):
        colour, words = badge[p["verdict"]]
        body = ""
        if p["verdict"] == "reject":
            why = ", ".join({"reversed": "it reversed a meaning", "swapped": "it named the wrong party",
                             "invented": "it named something the passage does not"}[k] for k in p["why_rejected"])
            body += f"<p><i>The automatic summary was withheld ({why}).</i> What this passage says:</p>"
            body += _fact_list(p["facts"]) or "<p>No facts were found here - please read the passage itself.</p>"
        else:
            body += f"<p style='font-size:1.05em'>{html.escape(p['summary'])}</p>"
            if p["missing"]:
                body += "<p>The summary leaves out:</p>" + _fact_list(p["missing"])
        source = html.escape(text[p["start"]:p["end"]]).replace("\n", "<br>")
        cards.append(f"<div style='border:1px solid #8884;border-radius:8px;padding:10px 14px;margin:10px 0'>"
                     f"<b>Passage {i}</b> <span style='background:{colour};color:#fff;border-radius:10px;padding:1px 8px;"
                     f"font-size:.85em'>{words}</span>{body}<details><summary>Read the passage</summary>"
                     f"<p style='opacity:.85'>{source}</p></details></div>")
    return "".join(cards)


def _consent_md(c: dict | None) -> str:
    if not c:
        return "_No consent artefact given._"
    day = lambda s: (s or "?")[:10]
    fmt = {
        "RECIPIENT": ("Who receives your data", lambda v: f"{v['id']} ({v['type']}, a coded id)"),
        "purpose": ("Why", lambda v: f"{v['text']} (code {v['code']})"),
        "DURATION": ("Consent valid", lambda v: f"{day(v['start'])} to {day(v['expiry'])}"),
        "FREQUENCY": ("How often data may be fetched", lambda v: f"up to {v['value']} time(s) per {v['unit'].lower()}"),
        "DATA_RANGE": ("Which period of your data", lambda v: f"{day(v['from'])} to {day(v['to'])}"),
        "DATA_LIFE": ("How long they may keep it", lambda v: f"{v['value']} {v['unit'].lower()}(s)"),
    }
    rows = [f"| {name} | {show(c[k]) if c.get(k) else '-'} |" for k, (name, show) in fmt.items()]
    return "| | |\n|---|---|\n" + "\n".join(rows) + f"\n\nOne-time or repeated: {c.get('fetch_type') or '-'}"


def analyse(text: str, upload, consent_text: str, record: bool):
    if upload is not None:
        text = read_document(Path(upload))
    try:
        text, r = _analyse_core(text, consent_text, record)
    except ValueError as e:
        raise gr.Error(str(e))
    seal = f"**Fingerprint of this policy + consent:** `{r['record_hash']}`"
    if r["chain"]:
        link = r["chain"]["audit_link"]
        seal += (f"\n\nRecorded on-chain. Consent id `{r['chain']['consent_id']}`"
                 + (f" - [view the transaction on Etherscan]({link})" if link else " (local test chain)"))
    seal += "\n\nKeep the report: checking this consent later needs the record inside it."
    return (f"**{summary_line(r).split(' | record')[0]}**", _highlights(text, r["facts"]), _passages_html(text, r),
            _consent_md(r["consent"]), seal, str(_save_report(r)))


def verify(consent_id: str, report_file):
    try:
        if not report_file:
            raise ValueError("Give the consent id and the report file.")
        try:
            record = json.loads(Path(report_file).read_text(encoding="utf-8"))["record"]
        except (KeyError, json.JSONDecodeError) as e:
            raise ValueError(f"Could not read the report: {e}")
        c = _check_core(consent_id, record)
    except ValueError as e:
        raise gr.Error(str(e))
    verdict = "VALID" if c["valid"] else "NOT VALID"
    return (f"### {verdict}\n| | |\n|---|---|\n| Status on-chain | {c['status']} |\n"
            f"| This record matches the one registered | {'yes' if c['hash_matches'] else 'NO - it was changed'} |\n"
            f"| Expired | {'yes' if c['expired'] else 'no'} |\n| Network | {c['chain_id']} |")


with gr.Blocks(title="ConsentLedger") as demo:
    gr.Markdown("# ConsentLedger\nWhat does this Account Aggregator policy really say - and can anyone change it later? "
                "_Research prototype; summaries are machine-written and checked automatically, so read the passage "
                "when it matters. Do not paste personal data._")
    with gr.Tab("Analyse a policy"):
        with gr.Row():
            with gr.Column():
                policy = gr.Textbox(label="Policy text", lines=12, placeholder="Paste the terms or privacy policy here")
                upload = gr.File(label="...or upload it (.txt, .html, .pdf)", file_types=[".txt", ".html", ".htm", ".pdf"], type="filepath")
            with gr.Column():
                consent = gr.Textbox(label="Consent artefact (ReBIT JSON, optional)", lines=12)
                record = gr.Checkbox(label="Record the fingerprint on the Sepolia test network", interactive=CAN_WRITE,
                                     info=None if CAN_WRITE else "Not configured on this server (needs a test wallet).")
        with gr.Row():
            example = gr.Button("Load an example")
            go = gr.Button("Analyse", variant="primary")
        headline = gr.Markdown()
        with gr.Tab("Highlighted policy"):
            marked = gr.HighlightedText(label="What the policy mentions", color_map=COLORS, combine_adjacent=False)
        with gr.Tab("Passage by passage"):
            cards = gr.HTML()
        with gr.Tab("Consent terms"):
            terms = gr.Markdown()
        with gr.Tab("Fingerprint and report"):
            seal = gr.Markdown()
            report = gr.File(label="Report (JSON)")
        example.click(lambda: (EXAMPLE_POLICY, DEMO_CONSENT), outputs=[policy, consent])
        go.click(analyse, [policy, upload, consent, record], [headline, marked, cards, terms, seal, report], concurrency_limit=1)
    with gr.Tab("Check a recorded consent"):
        gr.Markdown("Give the consent id and the report it came from. The record is fingerprinted again and compared "
                    "with the chain: change one word in the report and the check fails.")
        cid = gr.Textbox(label="Consent id (0x...)")
        rep = gr.File(label="Report (JSON)", file_types=[".json"], type="filepath")
        gr.Button("Check", variant="primary").click(verify, [cid, rep], gr.Markdown())


# ------------------------------------------------------------------ the JSON API for the web frontend
# Module level, so FastAPI can resolve the string annotations (`from __future__ import annotations`).
from fastapi import FastAPI, File, Form, HTTPException, UploadFile  # noqa: E402  (installed with gradio)
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse, RedirectResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402


class AnalyseIn(BaseModel):
    text: str
    consent: str = ""
    record: bool = False


class CheckIn(BaseModel):
    consent_id: str
    report: dict


def create_app():
    api = FastAPI(title="ConsentLedger API", docs_url="/api/docs", openapi_url="/api/openapi.json")
    # Only for developing the frontend on another local port (e.g. a live-reload server); same-origin needs none.
    api.add_middleware(CORSMiddleware, allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
                       allow_methods=["GET", "POST"], allow_headers=["*"])
    reports: dict[str, Path] = {}

    def result(text: str, r: dict) -> dict:
        rid = uuid.uuid4().hex
        reports[rid] = _save_report(r)
        return {"report_id": rid, "headline": summary_line(r).split(" | record")[0], "text": text, "report": r}

    def guarded(fn, *a):
        try:
            return fn(*a)
        except ValueError as e:                              # a problem with the input
            raise HTTPException(400, str(e))
        except (RuntimeError, ConnectionError) as e:         # e.g. the chain RPC is unreachable
            raise HTTPException(502, str(e))

    @api.get("/api/status")
    def status():
        return {"models_loaded": MODELS is not None, "chain_read": CAN_READ,
                "chain_write": CAN_WRITE and _writes < MAX_CHAIN_WRITES, "max_chars": MAX_CHARS, "max_file_mb": MAX_FILE_MB}

    @api.get("/api/demo")
    def demo_inputs():                                   # the same sample as the Gradio page's "Load an example"
        return {"policy": EXAMPLE_POLICY, "consent": DEMO_CONSENT}

    @api.post("/api/analyse")
    def api_analyse(body: AnalyseIn):
        return result(*guarded(_analyse_core, body.text, body.consent, body.record))

    @api.post("/api/analyse-file")
    def api_analyse_file(file: UploadFile = File(...), consent: str = Form(""), record: bool = Form(False)):
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in {".txt", ".html", ".htm", ".pdf"}:
            raise HTTPException(400, "Upload a .txt, .html or .pdf file.")
        data = file.file.read(MAX_FILE_MB * 2**20 + 1)
        if len(data) > MAX_FILE_MB * 2**20:
            raise HTTPException(400, f"The file is larger than {MAX_FILE_MB} MB.")
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / ("upload" + suffix)
            path.write_bytes(data)
            try:
                text = read_document(path)
            except Exception as e:                           # a broken or unreadable file
                raise HTTPException(400, f"Could not read the file: {e}")
        return result(*guarded(_analyse_core, text, consent, record))

    @api.post("/api/check")
    def api_check(body: CheckIn):
        return guarded(_check_core, body.consent_id, body.report.get("record", body.report))

    @api.get("/api/report/{rid}")
    def api_report(rid: str):
        path = reports.get(rid)
        if not path or not path.exists():
            raise HTTPException(404, "Report not found; reports last until the server restarts.")
        return FileResponse(path, media_type="application/json", filename="consentledger_report.json")

    app = gr.mount_gradio_app(api, demo, path="/gradio", max_file_size=f"{MAX_FILE_MB}mb")
    if (FRONTEND / "index.html").is_file():
        app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
    else:                                                    # e.g. a package without the frontend folder
        app.add_api_route("/", lambda: RedirectResponse("/gradio"), include_in_schema=False)
    return app


def _selfcheck() -> None:
    """The routes answer without loading any model (python app.py --selfcheck)."""
    from fastapi.testclient import TestClient
    c = TestClient(create_app())
    s = c.get("/api/status").json()
    assert set(s) >= {"models_loaded", "chain_read", "chain_write"}, s
    assert c.get("/").status_code == 200 and "ConsentLedger" in c.get("/").text
    assert c.get("/gradio/").status_code == 200
    assert c.post("/api/analyse", json={"text": "   "}).status_code == 400            # empty policy
    bad = c.post("/api/analyse", json={"text": "We collect PAN.", "consent": "{not json"})
    assert bad.status_code == 400 and "not valid JSON" in bad.json()["detail"], bad.text
    assert c.post("/api/analyse", json={"text": "x", "record": True}).status_code == 400   # record needs a consent
    assert c.post("/api/analyse-file", files={"file": ("a.exe", b"x")}).status_code == 400
    assert c.get("/api/report/nope").status_code == 404
    print("selfcheck ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        _selfcheck()
        sys.exit()
    _models()                                   # load once before the first visitor
    host = os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1")
    if "--gradio-only" in sys.argv:
        # --share: a temporary public https://....gradio.live link to this laptop (free; works while the app runs).
        # Set DEMO_PASSWORD to make visitors log in as "demo" with that password.
        password = os.environ.get("DEMO_PASSWORD")
        demo.launch(max_file_size=f"{MAX_FILE_MB}mb", server_name=host,
                    share="--share" in sys.argv, auth=("demo", password) if password else None)
    else:
        if "--share" in sys.argv:
            print("--share works only with the Gradio page: python app.py --gradio-only --share")
        import uvicorn
        print(f"ConsentLedger: http://{host}:7860  (backup Gradio page: http://{host}:7860/gradio)")
        uvicorn.run(create_app(), host=host, port=7860)
