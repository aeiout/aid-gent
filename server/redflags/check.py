import os, re, yaml

ROOT = os.path.dirname(os.path.dirname(__file__))
RULE_PATH = os.path.join(ROOT, "redflags", "rules_th.yaml")

class RedFlagChecker:
    def __init__(self):
        with open(RULE_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.rules = []
        for key, rule in data["rules"].items():
            pats = [re.compile(pat, flags=re.IGNORECASE) for pat in rule["patterns"]]
            self.rules.append({"label": rule["label"], "patterns": pats})

    def detect(self, text: str):
        t = (text or "").strip()
        if not t:
            return {"is_emergency": False, "label": None, "triggers": []}
        triggers = []
        label = None
        for rule in self.rules:
            for pat in rule["patterns"]:
                if pat.search(t):
                    triggers.append(pat.pattern)
                    label = rule["label"]
                    break
            if label:
                break
        return {"is_emergency": bool(label), "label": label, "triggers": triggers}
