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
  soap_summaries?: any[]; // from backend (array of soap_json objects)
  citations?: any[];
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

export async function createSession(intent?: "urti" | "derm"): Promise<CreateSessionResponse> {
  const res = await fetch(`${API_BASE}/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(intent ? { intent } : {}),
  });
  return handle(res);
}

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

export async function getTranscript(id: string): Promise<Transcript> {
  const res = await fetch(`${API_BASE}/session/${id}/transcript`, { cache: "no-store" });
  const data = await handle(res);
  return {
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
    soap_summaries: data.soap_summaries ?? [],
    citations: data.citations ?? [],
  };
}

export async function getSessionServerMeta(id: string): Promise<{
  intent?: string;
  ended: boolean;
  lastTs?: string;
}> {
  const res = await fetch(`${API_BASE}/session/${id}/transcript`, { cache: "no-store" });
  const data = await handle(res);

  const msgs: any[] = data.messages ?? [];
  let intent: string | undefined;
  for (let i = msgs.length - 1; i >= 0; i--) {
    const st = msgs[i]?.state;
    if (st && typeof st === "object" && st.intent) {
      intent = st.intent as string;
      break;
    }
  }
  const soapCount = (data.soap_summaries?.length ?? 0) as number;
  const ended =
    soapCount > 0 || (!!msgs.length && !!msgs[msgs.length - 1]?.state?.soap_ready === true);

  let lastTs: string | undefined = msgs.length ? msgs[msgs.length - 1]?.ts : undefined;
  if (lastTs && typeof lastTs !== "string") lastTs = new Date().toISOString();

  return { intent, ended, lastTs };
}
