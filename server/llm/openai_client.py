import os
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

class HostedModel:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"

    def chat(self, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=0.2
        )
        return resp.choices[0].message.content
