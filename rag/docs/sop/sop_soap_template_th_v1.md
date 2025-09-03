---
doc_id: sop_soap_template_th_v1
title: แม่แบบสรุปเคส SOAP (ภาษาไทย) และฟิลด์ข้อมูล
version: "1.0"
language: th-TH
category: sop
tags: ["SOAP","สรุปเคส","ฟิลด์"]
source: "Aid-gent SOP"
owner: "ทีมแพทย์ Aid-gent"
last_reviewed: "2025-09-03"
license: "Aid-gent internal use"
---

## รูปแบบแสดงผล (UI)
- ประเภทเคส, วันที่เวลา, สถานะธงแดง
- S: อาการหลัก/ระยะเวลา/ไข้/อาการร่วม/ปัจจัยเสี่ยง/สิ่งกระตุ้น
- O: ค่าที่ผู้ใช้รายงาน/รูปแนบ (ถ้ามี)
- A: ความเห็นเบื้องต้นแบบไม่วินิจฉัย + เหตุผลสั้น ๆ
- P: คำแนะนำทั่วไป, เกณฑ์พบแพทย์/ER, ข้อจำกัดของบอท

## ฟิลด์ JSON
อ้างอิงสคีม่า F3 (`schema_version`, `language`, `category`, `red_flag`, `subjective`, `objective`, `assessment`, `plan`, `attachments`, `knowledge_citations`, `meta`)
