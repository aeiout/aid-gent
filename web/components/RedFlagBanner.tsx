"use client";
export function RedFlagBanner({ message }: { message: string }) {
  return (
    <div className="mb-4 rounded-xl border-2 border-red-500 bg-red-50 p-3 text-sm text-red-700">
      <div className="font-semibold">พบสัญญาณอันตราย</div>
      <div className="mt-1">{message}</div>
      <a href="tel:1669" className="mt-2 inline-block rounded-lg bg-red-600 px-3 py-1 text-white">
        โทร 1669
      </a>
    </div>
  );
}
