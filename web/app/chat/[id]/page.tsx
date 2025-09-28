"use client";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { getTranscript, postChatTurn, Transcript } from "@/lib/api";
import { MessageList } from "@/components/MessageList";
import { Composer } from "@/components/Composer";
import { updateSession, touchSession } from "@/lib/sessionIndex";
import { RedFlagBanner } from "@/components/RedFlagBanner";
import Link from "next/link";

type Msg = { role: "user" | "assistant"; content_th: string; ts?: string };

export default function ChatPage() {
  const params = useParams();
  const id = useMemo(
    () => (Array.isArray(params?.id) ? params.id[0] : (params?.id as string)),
    [params]
  );
  const [messages, setMessages] = useState<Msg[]>([]);
  const [loading, setLoading] = useState(true);
  const [redFlag, setRedFlag] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [soapReady, setSoapReady] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const t: Transcript = await getTranscript(id);
        if (!mounted) return;
        setMessages(t.messages);
        // Ready if backend already produced any SOAP summaries
        if ((t.soap_summaries ?? []).length > 0) setSoapReady(true);
      } catch {
        setMessages([
          {
            role: "assistant",
            content_th: "ไม่สามารถโหลดบทสนทนา กรุณาลองใหม่",
            ts: new Date().toISOString(),
          },
        ]);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, [id]);

  async function onSend(text: string) {
    setSending(true);
    const ts = new Date().toISOString();
    setMessages((m) => [...m, { role: "user", content_th: text, ts }]);
    touchSession(id);

    try {
      const res = await postChatTurn({ session_id: id, user_text: text });
      if (res?.assistant_text) {
        setMessages((m) => [
          ...m,
          { role: "assistant", content_th: res.assistant_text, ts: new Date().toISOString() },
        ]);
      }
      if (res?.state?.red_flag_detected && res?.state?.red_flag_label) {
        setRedFlag("พบสัญญาณอันตราย (" + String(res.state.red_flag_label) + ")");
      }
      if (res?.state?.intent) {
        updateSession(id, { intent: res.state.intent });
      }
      if (res?.state?.soap_ready === true) {
        updateSession(id, { lastStatus: "ended", updatedAt: new Date().toISOString() });
      }
    } catch {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content_th: "เครือข่ายขัดข้อง ลองใหม่อีกครั้ง",
          ts: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div>
      {redFlag && <RedFlagBanner message={redFlag} />}

      {/* SOAP link when ready */}
      {soapReady && (
        <div className="mb-3 rounded-xl border bg-green-50 p-3 text-sm text-green-700">
          สรุป SOAP พร้อมแล้ว —{" "}
          <Link href={`/summary/${id}`} className="font-medium underline">
            ดูสรุป SOAP
          </Link>
        </div>
      )}

      {loading ? (
        <div className="text-sm text-gray-600">กำลังโหลด…</div>
      ) : (
        <>
          <MessageList messages={messages} />
          <Composer disabled={!!redFlag} loading={sending} onSend={onSend} />
        </>
      )}
    </div>
  );
}
