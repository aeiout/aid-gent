import { API_BASE } from "./env";

export type CreateSessionResponse = {
  session_id: string;
  intent?: "urti" | "derm";
};

export type ChatTurnResponse = {
  assistant_text: string;
  state: any;
};

export type Transcript = {
  session_id: string;
  messages: { role: "user" | "assistant"; content_th: string; ts: string }[];
};

async function handle(res: Response) {
  if (!res.ok) {
    let detail = "";
    try {
      detail = JSON.stringify(await res.json());
    } catch {}
    throw new Error(`${res.status} ${detail}`);
  }
  return res.json();
}

/** สร้าง session ใหม่ (แบ็กเอนด์ของคุณมี POST /session แล้ว) */
export async function createSession(intent?: "urti" | "derm"): Promise<CreateSessionResponse> {
  const res = await fetch(`${API_BASE}/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(intent ? { intent } : {}),
  });
  return handle(res);
}

/** ส่งข้อความในแชท (สอดคล้องกับ ChatTurnReq: { session_id?, user_text }) */
export async function postChatTurn(body: {
  session_id?: string;
  user_text: string;
}): Promise<ChatTurnResponse> {
  const res = await fetch(`${API_BASE}/chat/turn`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handle(res);
}

/** ดึง transcript แล้ว map ให้ FE ใช้ field content_th, ts ได้แน่ ๆ */
export async function getTranscript(id: string): Promise<Transcript> {
  const res = await fetch(`${API_BASE}/session/${id}/transcript`, { cache: "no-store" });
  const data = await handle(res);
  const mapped: Transcript = {
    session_id: data.session_id,
    messages: (data.messages || []).map((m: any) => ({
      role: m.role,
      content_th: m.content_th ?? m.text ?? "",
      ts:
        typeof m.ts === "string"
          ? m.ts
          : m.ts
          ? new Date(m.ts).toISOString()
          : new Date().toISOString(),
    })),
  };
  return mapped;
}
