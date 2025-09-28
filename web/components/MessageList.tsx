"use client";
import { useEffect, useRef } from "react";

type Msg = { role: "user" | "assistant"; content_th: string; ts?: string };

export function MessageList({ messages }: { messages: Msg[] }) {
  const endRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to newest message
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  return (
    <div className="flex max-h-[65vh] flex-col gap-3 overflow-y-auto pr-1">
      {messages.map((m, i) => (
        <div
          key={i}
          className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm leading-relaxed ${
            m.role === "user" ? "self-end bg-blue-600 text-white" : "self-start bg-gray-100"
          }`}
        >
          {m.content_th}
          {m.ts && (
            <div className="mt-1 text-[10px] opacity-60">
              {new Date(m.ts).toLocaleString("th-TH", {
                dateStyle: "medium",
                timeStyle: "short",
              })}
            </div>
          )}
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}
