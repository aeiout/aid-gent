import os
import yaml

ROOT = os.path.dirname(__file__)
CFG_DIR = os.path.join(ROOT, "config")

def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def load_system_prompt() -> str:
    return _read(os.path.join(CFG_DIR, "system_prompt_th.txt"))

def load_slot_policy() -> dict:
    with open(os.path.join(CFG_DIR, "slot_policy.yaml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_safety() -> dict:
    with open(os.path.join(CFG_DIR, "safety_strings.yaml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_rag_settings() -> dict:
    with open(os.path.join(CFG_DIR, "rag_settings.yaml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_slot_questions() -> dict:
    with open(os.path.join(CFG_DIR, "slot_questions_th.yaml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
