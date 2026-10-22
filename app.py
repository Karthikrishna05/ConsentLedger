"""ConsentLedger demo: paste an Account Aggregator policy (or upload it), optionally add the consent artefact,
and see what the policy says - highlighted facts, a checked plain-language summary per passage, the consent's
terms, and a tamper-proof fingerprint that can be recorded on the Sepolia test network.

It calls the same `pipeline.end_to_end.run()` as the experiments, so the demo and the reported numbers cannot
drift apart (bible 7.4). Research use only: the NER models were trained on non-commercial data (OPP-115).

    python app.py                      # http://127.0.0.1:7860
Settings come from the project's .env (see .env.example): SEPOLIA_RPC_URL for checking consents on-chain,
plus SEPOLIA_PRIVATE_KEY (a throwaway test wallet) to record them. Without them the app still runs.
"""
from __future__ import annotations

import html
import json
import os
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import gradio as gr  # noqa: E402

from consentledger.chain import web3_client  # noqa: E402,F401  (loads .env)
from consentledger.pipeline.end_to_end import load_models, read_document, run, summary_line  # noqa: E402

MAX_CHARS = 300_000                 # a long T&C is ~60k characters
MAX_CHAIN_WRITES = 20               # ponytail: per-process cap on test-ETH spend; a per-user limit if it goes public
CAN_READ = bool(os.environ.get("SEPOLIA_RPC_URL"))
CAN_WRITE = CAN_READ and bool(os.environ.get("SEPOLIA_PRIVATE_KEY"))
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


def _models():
    global MODELS
    with _lock:
        if MODELS is None:
            MODELS = load_models()
    return MODELS


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
    global _writes
    if upload is not None:
        text = read_document(Path(upload))
    text = (text or "").strip()
    if not text:
        raise gr.Error("Paste a policy or upload a .txt, .html or .pdf file.")
    if len(text) > MAX_CHARS:
        raise gr.Error(f"That document is {len(text):,} characters; the limit is {MAX_CHARS:,}.")
    artefact = None
    if (consent_text or "").strip():
        try:
            artefact = json.loads(consent_text)
        except json.JSONDecodeError as e:
            raise gr.Error(f"The consent artefact is not valid JSON: {e}")
        if not isinstance(artefact, dict):
            raise gr.Error("The consent artefact must be a JSON object.")
    chain = bool(record and artefact)
    if record and not artefact:
        raise gr.Error("Recording on-chain needs the consent artefact: its expiry is what the chain enforces.")
    if chain:
        with _lock:
            if not CAN_WRITE or _writes >= MAX_CHAIN_WRITES:
                raise gr.Error("Recording on-chain is not available on this server right now.")
            _writes += 1
    try:
        r = run(text, artefact, _models(), chain=chain)
    except ValueError as e:                     # e.g. an expired consent the chain refuses
        raise gr.Error(str(e))
    seal = f"**Fingerprint of this policy + consent:** `{r['record_hash']}`"
    if r["chain"]:
        link = r["chain"]["audit_link"]
        seal += (f"\n\nRecorded on-chain. Consent id `{r['chain']['consent_id']}`"
                 + (f" - [view the transaction on Etherscan]({link})" if link else " (local test chain)"))
    seal += "\n\nKeep the report: checking this consent later needs the record inside it."
    out = Path(tempfile.mkdtemp()) / "consentledger_report.json"
    out.write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
    return (f"**{summary_line(r).split(' | record')[0]}**", _highlights(text, r["facts"]), _passages_html(text, r),
            _consent_md(r["consent"]), seal, str(out))


def verify(consent_id: str, report_file):
    if not CAN_READ:
        raise gr.Error("Checking needs SEPOLIA_RPC_URL in the server's settings.")
    if not report_file or not (consent_id or "").strip():
        raise gr.Error("Give the consent id and the report file.")
    from consentledger.chain.read_consent import check
    try:
        record = json.loads(Path(report_file).read_text(encoding="utf-8"))["record"]
        c = check(consent_id.strip(), record)
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        raise gr.Error(f"Could not check: {e}")
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

if __name__ == "__main__":
    # _models()  # skipped: models not yet trained/uploaded; UI still loads for demo purposes
    # --share: a temporary public https://....gradio.live link to this laptop (free; works while the app runs).
    # Set DEMO_PASSWORD to make visitors log in as "demo" with that password.
    password = os.environ.get("DEMO_PASSWORD")
    demo.launch(max_file_size="10mb", server_name=os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1"),
                share="--share" in sys.argv, auth=("demo", password) if password else None)
