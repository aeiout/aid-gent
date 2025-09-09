# aid-gent

ผู้ช่วยคลินิก/สุขภาพ รวม RAG, triage, red-flags, LLM orchestration, SOP/education

- aid-gent/
  - app/ # Frontend app (empty for now)
  - server/ # FastAPI/uvicorn backend, RAG pipeline entrypoints
  - orchestrator/ # Orchestration / workflow
  - rag/ # RAG data, chunks, pipeline
  - redflags/ # Clinical red-flag rules
  - llm/ # Prompt templates, chains, tools
  - storage/ # Local storage (vector DB, caches, temp)
  - config/ # Put prompt/policy files here
  - docs/ # Internal docs
  - triage/ # Clinical triage logic/specs
  - education/ # Patient education contents
  - sop/ # SOPs, care-paths
  - index/ # Indexers, embedding jobs, scripts
  - snippets/ # Code/CLI snippets
  - qa/ # Evals & quality checks
  - ops/ # Ops/runbooks
  - README.md

---

# Quick Start (Windows/PowerShell)

## 1) Open PowerShell (pwsh recommended)

```bash
cd C:\Users\VICTUS\Desktop\aid-gent
```

## 2) Activate venv

```bash
.\.venv\Scripts\Activate.ps1
```

## 3) (Optional) Fix Thai text in classic PowerShell

```bash
chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
```

## 4) Run API (dev)

```bash
python -m uvicorn server.app:app --reload --port 8000
```

## 5) Open docs in browser

```bash
http://127.0.0.1:8000/docs
```

---

# Stop / Restart

## In the terminal where the server is running:

```bash
# Press twice if needed to stop

Ctrl + C
```

# (Optional) deactivate venv

```bash
deactivate
```

# Troubleshooting (Port 8000)

## Port 8000 stuck? Find PID then kill it

```bash
netstat -ano | findstr :8000
Stop-Process -Id <PID> -Force
```

# RAG: Re-ingest Documents

## ทำ หลัง จากแก้ไขไฟล์ใน rag/docs เท่านั้น

```bash
.\.venv\Scripts\Activate.ps1
python -m server.rag.ingest
```

# Reset Local Demo State

## ⚠️ ลบฐานข้อมูลโลคัลของเดโม (SQLite). หยุดเซิร์ฟเวอร์ก่อน

### Reset local state (demo cleanup)

```bash
Remove-Item .\aidgent.db
```

# API & Testing

## Test via Swagger UI

### Open in browser:

```bash
http://127.0.0.1:8000/docs

Use POST /chat/turn (keep the same session_id per conversation)
```

# Example: PowerShell Invoke-RestMethod

```bash
$body = @{
session_id = "demo-session-001"
message = "สวัสดี ช่วยประเมินอาการเจ็บคอให้หน่อย"
} | ConvertTo-Json

Invoke-RestMethod `  -Uri "http://127.0.0.1:8000/chat/turn"`
-Method POST `  -ContentType "application/json"`
-Body $body
```

# Example: curl

```bash
curl -X POST "http://127.0.0.1:8000/chat/turn" \
 -H "Content-Type: application/json" \
 -d '{
"session_id": "demo-session-001",
"message": "Hello, please triage sore throat."
}'
```
