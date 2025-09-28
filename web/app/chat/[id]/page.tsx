"use client";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { getTranscript, postChatTurn } from "@/lib/api";
import { MessageList } from "@/components/MessageList";
import { Composer } from "@/components/Composer";
import { touchSession } from "@/lib/sessionIndex";
import { RedFlagBanner } from "@/components/RedFlagBanner";

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

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const t = await getTranscript(id);
        if (!mounted) return;
        setMessages(t.messages);
      } catch (e: any) {
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
      // แบ็กเอนด์ของคุณตอบ assistant_text เสมอ
      if (res?.assistant_text) {
        setMessages((m) => [
          ...m,
          { role: "assistant", content_th: res.assistant_text, ts: new Date().toISOString() },
        ]);
      }
      // ถ้า state บอกว่าเป็น red-flag ให้โชว์แบนเนอร์ (แล้วแต่คุณจะใส่ flag ใน state ยังไง)
      if (res?.state?.red_flag_detected && res?.state?.red_flag_label) {
        setRedFlag("พบสัญญาณอันตราย (" + String(res.state.red_flag_label) + ")");
      }
    } catch (e) {
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
      {loading ? (
        <div className="text-sm text-gray-600">กำลังโหลด…</div>
      ) : (
        <>
          <MessageList messages={messages} />
          <Composer disabled={!!redFlag || sending} onSend={onSend} />
        </>
      )}
    </div>
  );
}
