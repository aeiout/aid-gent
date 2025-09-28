"use client";
import { useRouter } from "next/navigation";
import { createSession } from "@/lib/api";
import { addSession } from "@/lib/sessionIndex";

export default function HomePage() {
  const router = useRouter();

  async function startNewChat() {
    try {
      // กำหนด intent เริ่มต้นได้ (เดโม่: urti) หรือส่งว่างๆ ก็ได้
      const res = await createSession("urti");
      const now = new Date().toISOString();
      addSession({
        id: res.session_id,
        intent: res.intent,
        createdAt: now,
        updatedAt: now,
        lastStatus: "active",
      });
      router.push(`/chat/${res.session_id}`);
    } catch (err: any) {
      console.error("Failed to create session", err);
      alert("เริ่มแชทไม่สำเร็จ: " + (err?.message ?? err));
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Chat Bot ช่วยคัดกรองอาการ</h1>
      <p className="text-sm text-gray-600">
        ระบบนี้ให้คำแนะนำเบื้องต้น ไม่ใช่การวินิจฉัย หากมีอาการรุนแรงโปรดโทร 1669
      </p>
      <div className="flex gap-3">
        <button onClick={startNewChat} className="rounded-xl bg-blue-600 px-4 py-2 text-white">
          เริ่มแชทใหม่
        </button>
        <a href="/sessions" className="rounded-xl border px-4 py-2">
          ดูแชททั้งหมด
        </a>
      </div>
    </div>
  );
}
