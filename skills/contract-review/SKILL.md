---
name: contract-review
description: Review Vietnamese business contracts (hợp đồng mua bán, cung cấp dịch vụ, hợp đồng lao động, thuê nhà, EPC) under Vietnamese law — mandatory clauses, red flags, and a structured risk report. Use when the user asks to check a contract, "soát hợp đồng", or assess legal risk of a Vietnamese commercial contract.
---

# Contract Review (Vietnam)

Methodology for reviewing Vietnamese commercial contracts with an AI:
a repeatable checklist + risk report, not legal advice.

## When to use
- The user pastes or points to a contract in Vietnamese and asks to "soát",
  "review", "kiểm tra điều khoản", or "hợp đồng này có rủi ro gì không".
- The user is drafting a Vietnamese contract and wants a pre-signing check.

## Scope
- Vietnamese commercial and labor contracts; governing law: Vietnamese law
  for domestic contracts (Civil Code 2015 — BLDS; Commercial Law 2005 for
  traders — Luật Thương mại 2005; Labor Code 44/2025/QH15 for labor
  contracts).
- This is a **checklist + risk report**, never legal advice. For specific
  case decisions (litigation, large amounts, disputes), always end with:
  "Mang bản báo cáo này cho luật sư xác nhận trước khi ký."

## Workflow
1. Identify: contract type (mua bán / dịch vụ / lao động / thuê / EPC...),
   parties and their standing (MST, authorized signatory — compare the
   signatory's name with the company's registration/authorization letter if
   provided).
2. Walk the **mandatory clause checklist** below. For each clause:
   present / missing / weak.
3. Scan for **red flags** (below).
4. Output the risk report in the fixed format at the end.
5. Close with the disclaimer.

## Mandatory clause checklist
For every commercial contract:
- [ ] **Parties + legal standing**: full name, address, MST of each party;
      who signs and what authorizes them (Giấy ủy quyền).
- [ ] **Object + scope**: what is delivered, quantity, quality criteria
      (tiêu chuẩn/định mức) — vague "theo yêu cầu" without a spec is a risk.
- [ ] **Price + taxes**: clearly separate the VAT portion; currency;
      whether the price is fixed or adjustable, and on what basis.
- [ ] **Payment terms**: method (chuyển khoản vs. tiền mặt), deadline
      (within X working days of what event), late-payment interest.
      Flag: "chuyển khoản trong 60 ngày mà không nói mốc tính" (no anchor
      date) → unenforceable.
- [ ] **Liability for breach (trách nhiệm vi phạm)**: liquidated damages
      (phạt vi phạm) must be **≤ 8% of the value of the affected contract
      portion** (Art. 418(4) Civil Code 2015); compensation for actual
      damages (bồi thường) follows the actual loss.
- [ ] **Term + termination**: start/end dates or completion condition;
      termination grounds and notice period; consequences of early
      termination.
- [ ] **Dispute resolution**: negotiation first; then **either** arbitration
      (must name the arbitral body explicitly, e.g. VIAC, VNACCS — "trọng
      tài" without a named body is a defective clause) **or** the competent
      court. A clause naming both is contradictory.
- [ ] **Force majeure**: definition + notification duty + consequence.
- [ ] **Confidentiality / IP** (where relevant).
- [ ] **Governing law**: "Luật Việt Nam" for domestic deals.

Labor contracts (hợp đồng lao động, Labor Code 44/2025/QH15): check against
the labor-law skill — position, work location, term type (xác định / không
xác định thời hạn), working hours, wage, social insurance, probation terms.

## Red flags (auto-warn)
- One-sided liability: penalties for only one party.
- "Party A may terminate unilaterally without prior notice" with no
  compensation.
- Penalty clause > 8% of the affected portion (Art. 418(4) BLDS).
- Payment deadline with no anchor event and no cap.
- Auto-renewal clause without a no-renewal notice period.
- Dispute clause naming both court and arbitration.
- Signatory with no visible authorization document.
- Vague scope: no attached specification/appendix referenced by the scope
  clause.
- For 2026+ invoices: payment by cash ≥ 5,000,000 VND triggers extra VAT
  deduction scrutiny (Decree 181/2025) — flag cash payment terms on
  B2B deals.

## Risk report format
```
# Báo cáo rà soát hợp đồng
Hợp đồng: <tên/loại> — <Bên A> ⇄ <Bên B>
Ngày rà soát: <dd/MM/yyyy>
Cơ sở pháp lý áp dụng: BLDS 2015 / LTM 2005 / Luật LĐ 2025 (tùy loại)

## 1. Điều khoản bắt buộc
| # | Điều khoản | Trạng thái | Ghi chú |
|---|---|---|---|
| 1 | Bên + tư cách pháp lý | OK / Thiếu / Yếu | ... |
(…toàn bộ checklist…)

## 2. Red flags
| # | Điều | Vấn đề | Mức (cao/trung bình/thấp) | Căn cứ |
|---|---|---|---|---|

## 3. Kết luận
- Rủi ro lớn nhất (≤3 mục).
- Khuyên: ký sau khi sửa / ký được nhưng nên đàm phán / không nên ký.

## 4. Disclaimer
Đây là rà soát tự động theo checklist, không phải tư vấn pháp lý.
Bắt buộc có luật sư xác nhận trước khi ký.
```

## Rules for the AI performing the review
- Quote the clause text (trích dẫn nguyên văn, tối đa 2 dòng) next to every
  finding — the user must be able to locate it.
- Cite the article (Điều X, Luật Y) for every red flag; verify the article
  number against the consolidated text (Văn bản hợp nhất) before citing —
  do not cite from memory for article numbers you are not sure of.
- No price adjustment for long-term contracts (CPI): that is a negotiation
  point, not a legal defect — mark it as "đề xuất đàm phán", not "thiếu".
- Output language: match the user's (usually Vietnamese).
