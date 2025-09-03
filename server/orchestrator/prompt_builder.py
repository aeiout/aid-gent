from typing import List, Dict, Any
import json

def build_finalize_prompt(system_prompt: str, safety_strings: dict, slot_policy: dict,
                          snippets: List[Dict[str, Any]], slots: Dict[str, Any]):
    cited = []
    for sn in snippets:
        header = f"- {sn['doc_id']}:{sn.get('title','')} (v{sn.get('version','1.0')})"
        body = f"  [id: {sn['snippet_id']}] {sn['text']}"
        cited.append(header + "\n" + body)
    cited_block = "[CITED_SNIPPETS]\n" + "\n".join(cited) + "\n[END_CITED_SNIPPETS]" if cited else ""

    # STRONG instructions to finalize
    system = system_prompt + """
[STRICT MODE FINALIZE]
- ขณะนี้ข้อมูลครบทุกช่องแล้ว ห้ามถามคำถามเพิ่ม
- ให้สรุปผู้ใช้แบบสั้น/ชัดเจนเป็นภาษาไทย และให้คำแนะนำทั่วไปอิง CITED_SNIPPETS เท่านั้น
- ต้องส่ง [STATE_JSON] โดยตั้ง soap_ready=true และกรอก soap_json ให้ครบ (S/O/A/P)
- ห้ามสร้างข้อเท็จจริงเกินเอกสารอ้างอิง
"""

    user_block = (
        "[SLOTS_JSON]\n" + json.dumps(slots, ensure_ascii=False) + "\n[END_SLOTS_JSON]\n\n" +
        cited_block +
        "\nโปรดสรุปและให้คำแนะนำทั่วไปที่ปลอดภัย (แนบ footer ความปลอดภัย) พร้อม SOAP"
    )
    return {"system": system, "user": user_block}

def build_prompt(system_prompt: str, safety_strings: dict, slot_policy: dict,
                 snippets: List[Dict[str, Any]], history: List[Dict[str, str]], user_text: str):
    # format snippets
    cited = []
    for sn in snippets:
        header = f"- {sn['doc_id']}:{sn.get('title','')} (v{sn.get('version','1.0')})"
        body = f"  [id: {sn['snippet_id']}] {sn['text']}"
        cited.append(header + "\n" + body)
    cited_block = "[CITED_SNIPPETS]\n" + "\n".join(cited) + "\n[END_CITED_SNIPPETS]" if cited else ""

    # include minimal slot instructions inline to reduce drift
    slot_lines = [
        "นโยบาย Slot-complete (ย้ำสั้น ๆ):",
        "- ถ้าผู้ใช้ให้ข้อมูลบางช่องแล้ว ให้ยืนยันและข้าม",
        "- เก็บ Required slots ให้ครบก่อนให้คำแนะนำ",
        "- ครบแล้วให้คำแนะนำทั่วไปที่สอดคล้องกับ CITED_SNIPPETS และแนบ [STATE_JSON]"
    ]
    system = system_prompt + "\n\n" + "\n".join(slot_lines) + "\n"

    # minimal history (last 1-2 turns)
    history_lines = []
    for h in history[-4:]:
        role = "USER" if h["role"] == "user" else "ASSISTANT"
        history_lines.append(f"[{role}] {h['text']}")

    user_block = "\n".join(history_lines) + (("\n" if history_lines else "") + f"[USER] {user_text}\n\n") + cited_block

    return {"system": system, "user": user_block}
