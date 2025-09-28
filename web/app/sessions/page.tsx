"use client";
import { useEffect, useState } from "react";
import { listSessions, removeSession, SessionMeta, updateSession } from "@/lib/sessionIndex";
import { getSessionServerMeta } from "@/lib/api";
import {
  AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader,
  AlertDialogTitle, AlertDialogDescription, AlertDialogFooter,
  AlertDialogCancel, AlertDialogAction,
} from "@/components/ui/alert-dialog";

export default function SessionsPage() {
  const [items, setItems] = useState<SessionMeta[]>([]);
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  function refresh() { setItems(listSessions()); }

  useEffect(() => {
    refresh();
    // hydrate from server for accurate intent + status
    (async () => {
      const current = listSessions();
      await Promise.all(
        current.map(async (s) => {
          try {
            const meta = await getSessionServerMeta(s.id);
            updateSession(s.id, {
              intent: meta.intent ?? s.intent,
              lastStatus: meta.ended ? "ended" : "active",
              updatedAt: meta.lastTs ?? s.updatedAt,
            });
          } catch { /* ignore per-session errors */ }
        })
      );
      refresh();
    })();
  }, []);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 1800);
    return () => clearTimeout(t);
  }, [toast]);

  function onConfirmDelete(id: string) {
    removeSession(id);
    setPendingDelete(null);
    setToast("ลบแชทแล้ว");
    refresh();
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
                  เริ่มเมื่อ:{" "}
                  {new Date(s.createdAt).toLocaleString("th-TH", { dateStyle: "medium", timeStyle: "short" })}{" "}
                  · สถานะ: {s.lastStatus === "ended" ? "end" : "active"}
                </div>
                <div className="text-xs text-gray-600">
                  อาการ: {s.intent ? (s.intent === "derm" ? "ผิวหนัง" : "ทางเดินหายใจบน") : "-"}
                </div>
              </div>

              <div className="flex gap-2">
                <a href={`/chat/${s.id}`} className="rounded-lg border px-3 py-1 text-sm">เปิดดู</a>

                <AlertDialog open={pendingDelete === s.id} onOpenChange={(open) => setPendingDelete(open ? s.id : null)}>
                  <AlertDialogTrigger asChild>
                    <button className="rounded-lg bg-red-600 px-3 py-1 text-sm text-white">ลบ</button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>ยืนยันการลบแชท</AlertDialogTitle>
                      <AlertDialogDescription>
                        การลบนี้เป็นการลบเฉพาะในอุปกรณ์ของคุณ รายการนี้จะหายจากหน้ารายการแชท
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>ยกเลิก</AlertDialogCancel>
                      <AlertDialogAction className="bg-red-600 text-white hover:bg-red-700" onClick={() => onConfirmDelete(s.id)}>
                        ลบ
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </li>
          ))}
        </ul>
      )}

      {toast && <div className="fixed bottom-4 right-4 rounded-lg bg-black/90 px-3 py-2 text-sm text-white shadow-lg">{toast}</div>}
    </div>
  );
}
