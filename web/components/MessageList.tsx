"use client";

type Msg = { role: "user" | "assistant"; content_th: string; ts?: string };
export function MessageList({ messages }: { messages: Msg[] }) {
  return (
    <div className="flex flex-col gap-3">
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
              {new Date(m.ts).toLocaleString("th-TH")}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
