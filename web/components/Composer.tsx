"use client";
import { useState } from "react";

export function Composer({
  disabled,
  onSend,
}: {
  disabled?: boolean;
  onSend: (text: string) => Promise<void> | void;
}) {
  const [text, setText] = useState("");
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    const t = text;
    setText("");
    await onSend(t);
  }
  return (
    <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="พิมพ์คำตอบของคุณ…"
        className="flex-1 rounded-xl border px-3 py-2 focus:outline-none focus:ring"
        disabled={disabled}
      />
      <button
        type="submit"
        disabled={disabled}
        className="rounded-xl bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
      >
        ส่ง
      </button>
    </form>
  );
}
