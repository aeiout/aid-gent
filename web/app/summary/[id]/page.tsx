"use client";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { getTranscript, Transcript } from "@/lib/api";
import Link from "next/link";

type Soap = {
  subjective?: string;
  objective?: string;
  assessment?: string;
  plan?: string;
};

export default function SummaryPage() {
  const params = useParams();
  const id = useMemo(
    () => (Array.isArray(params?.id) ? params.id[0] : (params?.id as string)),
    [params]
  );

  const [loading, setLoading] = useState(true);
  const [soap, setSoap] = useState<Soap | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const data: Transcript = await getTranscript(id);
        // take latest soap object (API returns ascending)
        const raw = (data.soap_summaries || []).slice(-1)[0] ?? null;
        if (!mounted) return;
        setSoap(normalizeSoap(raw));
      } catch (e) {
        if (mounted) setError("ไม่สามารถโหลดสรุป SOAP ได้");
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [id]);

  if (loading) return <div className="text-sm text-gray-600">กำลังโหลดสรุป…</div>;
  if (error) return <div className="text-sm text-red-600">{error}</div>;
  if (!soap) {
    return (
      <div className="space-y-3">
        <div className="text-sm text-gray-600">ยังไม่มีสรุป SOAP สำหรับแชทนี้</div>
        <Link href={`/chat/${id}`} className="inline-block rounded-lg border px-3 py-1 text-sm">
          ย้อนกลับไปแชท
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl">
      {/* Header / actions */}
      <div className="mb-6 flex items-center justify-between print:hidden">
        <h1 className="text-xl font-semibold">สรุป SOAP</h1>
        <div className="flex gap-2">
          <Link href={`/chat/${id}`} className="rounded-lg border px-3 py-1 text-sm">
            ย้อนกลับไปแชท
          </Link>
          <button
            onClick={() => window.print()}
            className="rounded-lg bg-blue-600 px-3 py-1 text-sm text-white"
          >
            พิมพ์ / บันทึก PDF
          </button>
        </div>
      </div>

      {/* Sheet */}
      <div className="rounded-2xl border p-5 shadow-sm">
        <Section title="S — Subjective" body={soap.subjective} />
        <Section title="O — Objective" body={soap.objective} />
        <Section title="A — Assessment" body={soap.assessment} />
        <Section title="P — Plan" body={soap.plan} />
      </div>

      <p className="mt-4 text-xs text-gray-500 print:hidden">
        หมายเหตุ: เนื้อหานี้เป็นคำแนะนำเบื้องต้น ไม่ใช่การวินิจฉัย
      </p>
    </div>
  );
}

/** accept either {S,O,A,P} or {subjective,objective,assessment,plan} */
function normalizeSoap(raw: any): Soap | null {
  if (!raw || typeof raw !== "object") return null;
  const s = raw.subjective ?? raw.S ?? raw.s ?? (typeof raw === "string" ? raw : undefined);
  const o = raw.objective ?? raw.O ?? raw.o;
  const a = raw.assessment ?? raw.A ?? raw.a;
  const p = raw.plan ?? raw.P ?? raw.p;
  return {
    subjective: toText(s),
    objective: toText(o),
    assessment: toText(a),
    plan: toText(p),
  };
}

function toText(v: unknown): string | undefined {
  if (v == null) return "-";
  if (typeof v === "string") return v;
  try {
    return JSON.stringify(v, null, 2);
  } catch {
    return String(v);
  }
}

function Section({ title, body }: { title: string; body?: string }) {
  return (
    <div className="mb-5">
      <h2 className="mb-1 text-sm font-semibold">{title}</h2>
      <div className="whitespace-pre-wrap rounded-lg bg-white text-[13px] leading-relaxed">
        {body ?? "-"}
      </div>
      <div className="mt-3 h-px bg-gray-200" />
    </div>
  );
}
