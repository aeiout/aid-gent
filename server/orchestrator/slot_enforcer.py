from typing import Dict, Any, List
import re

# --- tiny Thai keyword maps for auto-extract ---
SYM_KEYWORDS = {
    "ไข้": ["ไข้"],
    "ไอ": ["ไอ"],
    "เจ็บคอ": ["เจ็บคอ"],
    "น้ำมูก": ["น้ำมูก", "น้ำมูกไหล", "คัดจมูก"],
    "ผื่น": ["ผื่น", "ลมพิษ", "ตุ่ม", "ตุ่มน้ำ", "ปื้นแดง"],
    "คัน": ["คัน"],
}

THAI_NUM_WORDS = {
    "ศูนย์": 0, "หนึ่ง": 1, "สอง": 2, "สาม": 3, "สี่": 4, "ห้า": 5,
    "หก": 6, "เจ็ด": 7, "แปด": 8, "เก้า": 9, "สิบ": 10, "สิบเอ็ด": 11, "สิบสอง": 12,
}
DUR_UNITS = r"(วัน|ชั่วโมง|ชม\.|ช\.ม\.|สัปดาห์|อาทิตย์|เดือน)"

def _thai_words_to_number(text: str) -> str:
    # very small normalizer
    rep = [("สิบเอ็ด","11"), ("สิบสอง","12")]
    for w, n in rep:
        text = text.replace(w, n)
    for w, n in THAI_NUM_WORDS.items():
        text = text.replace(w, str(n))
    return text

def _is_filled(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() != "" and v != "null"
    if isinstance(v, (list, dict, set, tuple)):
        return len(v) > 0
    return True  # numbers/bools are meaningful

def _meaningful(v: Any) -> bool:
    # False and 0 are meaningful updates; None/""/[] are not
    if isinstance(v, bool):
        return True
    return _is_filled(v)

def _get_ask_order(intent_cfg: Dict[str, Any]) -> List[str]:
    return intent_cfg.get("ask_order", intent_cfg.get("required_slots", []))

def auto_fill_main_symptoms_from_text(user_text: str, slots: Dict[str, Any]) -> None:
    if slots.get("main_symptoms"):
        return
    found = []
    t = (user_text or "").strip()
    for label, kws in SYM_KEYWORDS.items():
        for kw in kws:
            if kw in t:
                found.append(label); break
    if found:
        slots["main_symptoms"] = list(dict.fromkeys(found))

def fold_boolean_symptoms_into_main(slots: Dict[str, Any]) -> None:
    # If model output had booleans like fever/cough/sore_throat, fold into main_symptoms
    mapping = {
        "fever": "ไข้",
        "cough": "ไอ",
        "sore_throat": "เจ็บคอ",
        "runny_nose": "น้ำมูก",
        "rash": "ผื่น",
    }
    arr = list(slots.get("main_symptoms") or [])
    for k, label in mapping.items():
        val = slots.get(k)
        if isinstance(val, bool) and val is True and label not in arr:
            arr.append(label)
    if arr:
        slots["main_symptoms"] = arr

DERM_SYM = {"ผื่น", "คัน"}
RESP_SYM = {"ไข้", "ไอ", "เจ็บคอ", "น้ำมูก"}

def refine_main_symptoms_for_intent(intent: str, slots: Dict[str, Any]) -> None:
    arr = list(slots.get("main_symptoms") or [])
    if not arr:
        # หากมี slot boolean ของผื่นให้เติม 'ผื่น'
        if intent == "derm_rash" and slots.get("rash") is True:
            slots["main_symptoms"] = ["ผื่น"]
        return
    if intent == "derm_rash":
        arr = [s for s in arr if s in DERM_SYM]
        if slots.get("rash") is True and "ผื่น" not in arr:
            arr.append("ผื่น")
    elif intent == "resp_upper":
        arr = [s for s in arr if s in RESP_SYM]
    slots["main_symptoms"] = arr

def auto_fill_duration_from_text(user_text: str, slots: Dict[str, Any]) -> None:
    if slots.get("duration"):
        return
    t = (user_text or "").strip()
    if not t:
        return
    t_norm = _thai_words_to_number(t)
    m = re.search(r"(\d+(?:\.\d+)?)\s*" + DUR_UNITS, t_norm)
    if m:
        num = m.group(1); unit = m.group(2)
        slots["duration"] = f"{num} {unit}"

def normalize_unknowns(user_text: str, slots: Dict[str, Any]) -> None:
    t = (user_text or "").lower()
    unknown_markers = ["ไม่ทราบ", "ไม่ได้วัด", "ไม่มีเทอร์โมมิเตอร์", "ไม่มีที่วัดไข้"]
    if any(x in t for x in unknown_markers):
        slots["fever_measured"] = False
        slots["fever_max_c"] = None
        slots["fever_method"] = None

def compute_missing(intent: str, slots: Dict[str, Any], slot_policy: Dict[str, Any]) -> List[str]:
    intents = slot_policy.get("intents", {})
    cfg = intents.get(intent, {})
    required = cfg.get("required_slots", [])
    conds = cfg.get("conditional_required", [])

    missing = [name for name in required if not _is_filled(slots.get(name))]

    # conditional requirements
    for rule in conds:
        cond = (rule.get("if") or "").replace("true", "True").replace("false", "False")
        then = rule.get("then", [])
        try:
            local = {"__builtins__": {}}
            local.update(slots)
            ok = bool(eval(cond, {}, local))
        except Exception:
            ok = False
        if ok:
            for name in then:
                if not _is_filled(slots.get(name)) and name not in missing:
                    missing.append(name)

    order = _get_ask_order(cfg)
    missing.sort(key=lambda x: order.index(x) if x in order else 999)
    return missing

def merge_states(prev: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(prev or {})
    prev_intent = out.get("intent")
    new_intent = (new or {}).get("intent")

    # เลือก intent ใหม่ถ้าชัด
    if new_intent and new_intent != "uncertain":
        intent = new_intent
    else:
        intent = prev_intent or new_intent or "uncertain"
    intent_changed = bool(prev_intent and new_intent and new_intent != prev_intent)
    out["intent"] = intent

    # merge slots
    ps = dict(prev.get("slots") or {})
    ns = dict(new.get("slots") or {})
    for k, v in ns.items():
        if _meaningful(v) or isinstance(v, bool):
            ps[k] = v

    if intent_changed:
        # ช่องที่คงไว้ได้ทุก intent
        keep_general = {"risk_factors", "meds_allergies"}

        derm_only = {
            "rash", "rash_morphology", "rash_location_primary",
            "rash_extent", "associated", "suspected_triggers", "vulnerable_groups"
        }
        resp_only = {
            "fever", "cough", "sore_throat", "runny_nose",
            "fever_measured", "fever_max_c", "fever_method"
        }

        # ลบช่องที่ไม่เข้ากับ intent ใหม่
        drop = resp_only if intent == "derm_rash" else derm_only
        for k in list(ps.keys()):
            if k in drop and k not in keep_general:
                ps.pop(k, None)

        # ล้าง main_symptoms เพื่อให้ re-extract ตาม intent ใหม่
        ps.pop("main_symptoms", None)

        # reset asked slots
        out["asked_slots"] = []

    out["slots"] = ps

    # asked_slots: union เว้นแต่ intent เปลี่ยน
    asked_prev = set(prev.get("asked_slots") or [])
    asked_new = set(new.get("asked_slots") or [])
    out["asked_slots"] = [] if intent_changed else list(asked_prev | asked_new)

    return out

    out = dict(prev or {})
    # intent: prefer new if provided (and not 'uncertain')
    new_intent = (new or {}).get("intent")
    if new_intent and new_intent != "uncertain":
        out["intent"] = new_intent
    else:
        out["intent"] = out.get("intent") or new_intent or "uncertain"

    # slots merge (meaningful updates override, but don't drop prior values)
    ps = dict(prev.get("slots") or {})
    ns = dict(new.get("slots") or {})
    for k, v in ns.items():
        if _meaningful(v) or isinstance(v, bool):
            ps[k] = v
    out["slots"] = ps

    # asked_slots: union
    asked_prev = set(prev.get("asked_slots") or [])
    asked_new = set(new.get("asked_slots") or [])
    out["asked_slots"] = list(asked_prev | asked_new)

    # after computing new_intent
    if prev.get("intent") and new_intent and new_intent != prev["intent"]:
        out["asked_slots"] = []  # reset asked list on intent change

    return out

def enforce_state(prev_state: Dict[str, Any], new_state: Dict[str, Any],
                  slot_policy: Dict[str, Any], slot_questions: Dict[str, Any],
                  user_view_from_llm: str, last_user_text: str):
    # Merge previous + new
    state = merge_states(prev_state or {}, new_state or {})
    intent = state.get("intent") or "uncertain"
    slots = state.get("slots") or {}

    # --- alias normalization (so 'severity' becomes 'severity_overall', etc.) ---
    alias_map = {
        "severity": "severity_overall",
        "symptoms": "co_symptoms",        # if model used a generic key
        "medications": "meds_allergies",  # coarse map; still acceptable for required filled check
    }
    for k_src, k_dst in alias_map.items():
        if k_src in slots and k_dst not in slots:
            slots[k_dst] = slots[k_src]
    
    # Normalize / auto-extract
    auto_fill_main_symptoms_from_text(last_user_text, slots)
    fold_boolean_symptoms_into_main(slots)
    auto_fill_duration_from_text(last_user_text, slots)
    normalize_unknowns(last_user_text, slots)
    refine_main_symptoms_for_intent(intent, slots)

    # Compute missing, skip what we've already asked
    asked = set(state.get("asked_slots") or [])
    missing = compute_missing(intent, slots, slot_policy)
    missing = [m for m in missing if m not in asked]

    # Write truth back
    state["slots"] = slots
    state["missing_slots"] = missing
    state["required_slots_filled"] = len(missing) == 0

    if missing:
        next_slot = missing[0]                       # ONE slot per turn
        asked.add(next_slot)
        state["asked_slots"] = list(asked)
        state["soap_ready"] = False
        state["soap_json"] = {}
        # Question text
        qmap = slot_questions.get(intent, {})
        question = qmap.get(next_slot) or "ขอข้อมูลเพิ่มเติมเพื่อเก็บรายละเอียดอาการให้ครบค่ะ"
        return question, state

    # All required slots present → allow LLM's Thai guidance/SOAP to pass through
    return user_view_from_llm, state
