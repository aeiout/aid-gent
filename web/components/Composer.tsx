"use client";
import { useState } from "react";

export function Composer({
  disabled,
  loading,
  onSend,
}: {
  disabled?: boolean;
  loading?: boolean;
  onSend: (text: string) => Promise<void> | void;
}) {
  const [text, setText] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim() || disabled || loading) return;
    const t = text;
    setText("");
    await onSend(t);
  }

  return (
    <form onSubmit={handleSubmit} className="mt-4 space-y-1">
      <div className="flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="พิมพ์ข้อความ…"
          className="flex-1 rounded-xl border px-3 py-2 focus:outline-none focus:ring"
          disabled={disabled || loading}
        />
        <button
          type="submit"
          disabled={disabled || loading}
          className="rounded-xl bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
        >
          {loading ? "กำลังส่ง…" : "ส่ง"}
        </button>
      </div>
      {loading && <div className="pl-1 text-xs text-gray-500">กำลังส่ง… โปรดรอสักครู่</div>}
    </form>
  );
}
