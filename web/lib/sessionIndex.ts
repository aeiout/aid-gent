export type SessionMeta = {
  id: string;
  intent?: "urti" | "derm";
  createdAt: string; // ISO
  updatedAt: string; // ISO
  lastStatus: "active" | "ended";
};

const KEY = "aidgent:sessions";

function read(): SessionMeta[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as SessionMeta[]) : [];
  } catch {
    return [];
  }
}

function write(list: SessionMeta[]) {
  localStorage.setItem(KEY, JSON.stringify(list));
}

export function listSessions(): SessionMeta[] {
  return read().sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

export function addSession(meta: SessionMeta) {
  const list = read();
  const filtered = list.filter((s) => s.id !== meta.id);
  filtered.unshift(meta);
  write(filtered);
}

export function removeSession(id: string) {
  const list = read().filter((s) => s.id !== id);
  write(list);
}

export function touchSession(id: string) {
  const list = read();
  const i = list.findIndex((s) => s.id === id);
  if (i >= 0) {
    list[i].updatedAt = new Date().toISOString();
    write(list);
  }
}
