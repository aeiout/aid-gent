export const metadata = { title: "aid-gent demo", description: "Thai-first triage demo" };
import "./globals.css";
import Link from "next/link";
import { Providers } from "./providers";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="th">
      <body className="min-h-screen bg-white text-gray-900">
        <Providers>
          <header className="border-b">
            <div className="mx-auto max-w-3xl px-4 py-3 flex items-center justify-between">
              <Link href="/" className="font-semibold">
                aid-gent
              </Link>
              <nav className="text-sm flex gap-4">
                <Link href="/">หน้าแรก</Link>
                <Link href="/sessions">แชททั้งหมด</Link>
              </nav>
            </div>
          </header>
          <main className="mx-auto max-w-3xl px-4 py-6">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
