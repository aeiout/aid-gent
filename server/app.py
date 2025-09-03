import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()

from server.config_loader import load_system_prompt, load_slot_policy, load_safety, load_rag_settings
from server.config_loader import load_slot_questions
from server.orchestrator.slot_enforcer import enforce_state
from server.redflags.check import RedFlagChecker
from server.rag.search import RagSearcher
from server.llm.openai_client import HostedModel
from server.orchestrator.prompt_builder import build_prompt, build_finalize_prompt
from server.storage.db import init_db, SessionLocal
from server.storage.models import Message, SessionRec, SoapSummary, Citation

app = FastAPI(title="Aid-gent Prototype API", version="0.1")

# CORS (loose for prototype)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

# --- load configs ---
SYSTEM_PROMPT = load_system_prompt()
SLOTS = load_slot_policy()
SAFETY = load_safety()
RAGCFG = load_rag_settings()
QUESTIONS = load_slot_questions()

# --- init services ---
checker = RedFlagChecker()          # deterministic rules from YAML (bundled)
searcher = RagSearcher(RAGCFG)      # Pinecone + OpenAI embeddings
hosted = HostedModel()              # GPT-4o client

# --- init DB ---
init_db()

# ---------- Schemas ----------
class ChatTurnReq(BaseModel):
    session_id: Optional[str] = None
    user_text: str
    locale: Optional[str] = "th-TH"

class ChatTurnResp(BaseModel):
    assistant_text: str
    state: Dict[str, Any]

# ---------- Helpers ----------
def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_recent_history(db, session_id: str, max_turns: int = 2) -> List[Dict[str, str]]:
    msgs = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at.desc()).limit(max_turns*2).all()
    history = []
    for m in reversed(msgs):
        history.append({"role": m.role, "text": m.text})
    return history

def get_last_state(db, session_id: str) -> Dict[str, Any]:
    from server.storage.models import Message
    m = db.query(Message).filter(
        Message.session_id == session_id,
        Message.role == "assistant"
    ).order_by(Message.created_at.desc()).first()
    if not m or not m.state_json:
        return {}
    try:
        import json
        return json.loads(m.state_json)
    except Exception:
        return {}


def parse_llm_output(raw_text: str) -> (str, Dict[str, Any]):
    """
    Split the model output into [USER_VIEW] and [STATE_JSON]
    """
    user_view = ""
    state_json: Dict[str, Any] = {}
    text = raw_text

    # Find markers
    uv_start = text.find("[USER_VIEW]")
    sj_start = text.find("[STATE_JSON]")

    if uv_start != -1 and sj_start != -1:
        user_view = text[uv_start + len("[USER_VIEW]"):sj_start].strip()
        state_str = text[sj_start + len("[STATE_JSON]"):].strip()
        # trim code fences if any
        if state_str.startswith("```"):
            state_str = state_str.split("```", 2)[1] if "```" in state_str[3:] else state_str[3:]
        # attempt json parse
        try:
            state_json = json.loads(state_str)
        except Exception:
            # try to extract first {...}
            first_brace = state_str.find("{")
            last_brace = state_str.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                try:
                    state_json = json.loads(state_str[first_brace:last_brace+1])
                except Exception:
                    state_json = {}
    else:
        # fallback: whole thing to user, empty state
        user_view = raw_text
        state_json = {}

    return user_view, state_json

# ---------- Routes ----------
@app.post("/chat/turn", response_model=ChatTurnResp)
def chat_turn(req: ChatTurnReq):
    user_text = (req.user_text or "").strip()
    if not user_text:
        raise HTTPException(400, "user_text required")

    with SessionLocal() as db:
        # ensure session
        sid = req.session_id or f"temp_{datetime.utcnow().timestamp()}"
        if not (db.query(SessionRec).filter(SessionRec.id == sid).first()):
            db.add(SessionRec(id=sid, created_at=now_iso(), age_bucket="unknown", consent_flags="{}"))
            db.commit()

        # log user message
        msg_user = Message(session_id=sid, role="user", text=user_text, state_json="{}", created_at=now_iso())
        db.add(msg_user); db.commit()

        # Tier 0: deterministic red flags (no LLM if emergency)
        rf = checker.detect(user_text)
        if rf["is_emergency"]:
            assistant_text = SAFETY["emergency_main"]
            state = {
                "intent": "emergency",
                "required_slots_filled": False,
                "missing_slots": [],
                "slots": {},
                "red_flag_detected": True,
                "red_flag_label": rf["label"],
                "citations": [],
                "soap_ready": False
            }
            # persist assistant + end
            msg_ai = Message(session_id=sid, role="assistant", text=assistant_text, state_json=json.dumps(state), created_at=now_iso())
            db.add(msg_ai); db.commit()
            return ChatTurnResp(assistant_text=assistant_text, state=state)

        # RAG: search snippets
        snippets = searcher.search(user_text, top_k=RAGCFG["search"]["k"], min_score=RAGCFG["search"]["min_score"], mmr=RAGCFG["search"]["mmr"])

        # Build prompt
        history = get_recent_history(db, sid, max_turns=2)
        prompt = build_prompt(
            system_prompt=SYSTEM_PROMPT,
            safety_strings=SAFETY,
            slot_policy=SLOTS,
            snippets=snippets,
            history=history,
            user_text=user_text
        )

        # LLM call
        completion = hosted.chat(system=prompt["system"], user=prompt["user"])
        user_view, state_json = parse_llm_output(completion)
        prev_state = get_last_state(db, sid)
        user_view, state_json = enforce_state(prev_state, state_json or {}, SLOTS, QUESTIONS, user_view, user_text)

        if not user_view:
            raise HTTPException(500, "LLM output parse error")

        # If required slots are complete but LLM didn't finalize, force a finalize pass
        if state_json.get("required_slots_filled") and not state_json.get("soap_ready"):
            fin = build_finalize_prompt(
                system_prompt=SYSTEM_PROMPT,
                safety_strings=SAFETY,
                slot_policy=SLOTS,
                snippets=snippets,
                slots=state_json.get("slots", {})
        )
        completion2 = hosted.chat(system=fin["system"], user=fin["user"])
        user_view2, state2 = parse_llm_output(completion2)

        # Safety net: if the second pass still didn't provide soap_json, we still stop asking
        if not state2:
            state2 = state_json
        state2["soap_ready"] = True if state2.get("soap_json") else True
        state2["required_slots_filled"] = True
        # mark everything as asked so we never ask again
        intents_cfg = SLOTS.get("intents", {}).get(state2.get("intent",""), {})
        all_required = intents_cfg.get("required_slots", [])
        state2["asked_slots"] = list(set(state2.get("asked_slots", []) + all_required))

        # replace response with finalized one
        user_view = user_view2 or user_view
        state_json = state2

        # persist assistant
        msg_ai = Message(session_id=sid, role="assistant", text=user_view, state_json=json.dumps(state_json), created_at=now_iso())
        db.add(msg_ai); db.commit()

        # persist SOAP + citations if present
        if state_json.get("soap_ready") and state_json.get("soap_json"):
            db.add(SoapSummary(session_id=sid, soap_json=json.dumps(state_json["soap_json"]), created_at=now_iso()))
            db.commit()
        if state_json.get("citations"):
            for cit in state_json["citations"]:
                db.add(Citation(session_id=sid, turn_id=msg_ai.id, doc_id=cit.get("doc_id",""), snippet_ids=",".join(cit.get("snippet_ids",[]))))
            db.commit()

        return ChatTurnResp(assistant_text=user_view, state=state_json)

class ReindexReq(BaseModel):
    force: bool = True

@app.post("/rag/reindex")
def reindex(_: ReindexReq):
    ok = searcher.ingest_all()
    return {"indexed_docs": ok["docs"], "chunks": ok["chunks"]}

@app.get("/session/{session_id}/transcript")
def transcript(session_id: str):
    with SessionLocal() as db:
        msgs = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at.asc()).all()
        out = [{"role": m.role, "text": m.text, "state": json.loads(m.state_json)} for m in msgs]
        soaps = db.query(SoapSummary).filter(SoapSummary.session_id == session_id).order_by(SoapSummary.created_at.asc()).all()
        cites = db.query(Citation).filter(Citation.session_id == session_id).order_by(Citation.turn_id.asc()).all()
        return {
            "session_id": session_id,
            "messages": out,
            "soap_summaries": [json.loads(s.soap_json) for s in soaps],
            "citations": [{"turn_id": c.turn_id, "doc_id": c.doc_id, "snippet_ids": c.snippet_ids.split(",") if c.snippet_ids else []} for c in cites]
        }
