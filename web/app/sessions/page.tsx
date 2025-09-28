"use client";
import { useEffect, useState } from "react";
import { listSessions, removeSession, SessionMeta } from "@/lib/sessionIndex";

export default function SessionsPage() {
  const [items, setItems] = useState<SessionMeta[]>([]);
  function refresh() {
    setItems(listSessions());
  }
  useEffect(() => {
    refresh();
  }, []);

  function onDelete(id: string) {
    if (confirm("ยืนยันการลบแชทนี้หรือไม่? การลบนี้เป็นการลบเฉพาะในอุปกรณ์ของคุณ")) {
      removeSession(id);
      refresh();
    }
  }

  return (
    <div>
      <h1 className="mb-4 text-xl font-semibold">แชทของฉัน</h1>
      {items.length === 0 ? (
        <div className="text-sm text-gray-600">ยังไม่มีแชท เริ่มแชทใหม่ได้เลย</div>
      ) : (
        <ul className="space-y-3">
          {items.map((s) => (
            <li key={s.id} className="flex items-center justify-between rounded-xl border p-3">
              <div>
                <div className="font-medium">ID: {s.id}</div>
                <div className="text-xs text-gray-600">
                  เริ่มเมื่อ: {new Date(s.createdAt).toLocaleString("th-TH")} · สถานะ:{" "}
                  {s.lastStatus}
                </div>
                {s.intent && (
                  <div className="text-xs text-gray-600">
                    อาการ: {s.intent === "urti" ? "ทางเดินหายใจบน" : "ผิวหนัง"}
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <a href={`/chat/${s.id}`} className="rounded-lg border px-3 py-1 text-sm">
                  เปิดดู
                </a>
                <button
                  onClick={() => onDelete(s.id)}
                  className="rounded-lg bg-red-600 px-3 py-1 text-sm text-white"
                >
                  ลบ
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
