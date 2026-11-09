# vietskills

**Agent skills for Vietnamese business workflows.** A skill pack that
teaches coding agents (Claude Code, Codex, Cursor, Gemini CLI…) how to do
the paperwork every Vietnamese company does — correctly:

| Skill | What it does |
|---|---|
| `e-invoice` | Validates a Vietnamese e-invoice XML (hóa đơn điện tử) — structure, arithmetic, dates, MST format — and maps every error to the legally correct fix (điều chỉnh / thay thế / thông báo sai sót) |
| `payroll-tax` | Computes monthly payroll: mandatory insurance (10.5% / 21.5%) + personal income tax under the 2026 rules (PIT Law 109/2025/QH15, 5-bracket table, 15.5M/6.2M deductions) — with a tested Python API |
| `contract-review` | A repeatable Vietnamese contract review: mandatory-clause checklist, red flags (penalty > 8% per Art. 418(4) BLDS, defective dispute clauses, …), and a fixed risk-report format |
| `labor-law` | Quick compliance table for the 2025 Labor Code (44/2025/QH15): probation, working hours, overtime, leave, termination notice |

The differentiator: **every legal fact is cited to a specific decree,
circular, or law**, with the rule of "verify the consolidated text before
citing article numbers" baked into the workflow. The two computational
skills ship runnable, **tested** Python scripts — not prose the agent has to
re-derive every time.

> All skills are rule references as of **November 2026**. Vietnamese tax and
> invoice rules change by circular — re-verify the dates before relying on
> any figure in production.

## Install

Skills are folders of `SKILL.md` + optional scripts. Copy them into your
agent's skill directory:

```bash
# Claude Code (personal)
cp -r skills/* ~/.claude/skills/
# Claude Code (per project)
cp -r skills/* .claude/skills/

# Codex
cp -r skills/* ~/.codex/skills/

# Gemini CLI
gemini skills install <this-repo> --path skills   # or copy manually
```

Or clone the repo once and point your agent at `skills/`:

```bash
git clone https://github.com/<you>/vietskills.git
```

Each skill is self-contained: the `SKILL.md` tells the agent *when* to use
it, *how* to run the scripts, and *what* to say in the output.

## Try it

```bash
# 1. Validate a sample e-invoice (see skills/e-invoice for a valid XML)
python skills/e-invoice/scripts/validate_hd.py sample_invoice.xml

# 2. Compute a 2026 payroll (gross 25M, 1 dependent, August 2026)
python skills/payroll-tax/scripts/payroll.py \
    --gross 25000000 --month 2026-08 --dependents 1
```

## Tests

No dependencies (stdlib only). Run everything from the repo root:

```bash
python skills/e-invoice/scripts/test_validate_hd.py
python skills/payroll-tax/scripts/test_payroll.py
```

## Structure

```
skills/
├── e-invoice/
│   ├── SKILL.md
│   └── scripts/
│       ├── validate_hd.py      # DonHieu XML validator (stdlib only)
│       └── test_validate_hd.py
├── payroll-tax/
│   ├── SKILL.md
│   └── scripts/
│       ├── payroll.py          # PayStub API + CLI
│       └── test_payroll.py
├── contract-review/
│   └── SKILL.md
└── labor-law/
    └── SKILL.md
```

## Contributing

Pull requests welcome. Rules:

1. Every legal claim needs a citation (law/decree/circular + article).
2. Computational rules must come with a passing test.
3. `SKILL.md` frontmatter `description` is the trigger — keep it specific
   (include the Vietnamese phrases users actually type).
4. State the "as of" date of every rule set.

## Disclaimer

These skills encode rules for reference and automation. They are **not legal
advice**. Always have a qualified lawyer confirm before signing contracts or
filing tax declarations.

---

## Tiếng Việt

**Bộ skill cho agent AI làm việc với nghiệp vụ doanh nghiệp Việt Nam.**
Dạy cho coding agent (Claude Code, Codex, Cursor, Gemini CLI…) cách xử lý
đúng các giấy tờ mà doanh nghiệp VN nào cũng gặp:

| Skill | Làm gì |
|---|---|
| `e-invoice` | Kiểm tra hóa đơn điện tử (file XML `DonHieu`): cấu trúc, số học, ngày tháng, định dạng MST — và đưa ra cách xử lý đúng luật cho từng lỗi (điều chỉnh / thay thế / thông báo sai sót theo TT 91/2026, TT 78/2021) |
| `payroll-tax` | Tính lương tháng: BHXH/BHYT/BHTN (10,5% NLĐ / 21,5% NSDLĐ, trần 20× lương cơ sở) + thuế TNCN theo Luật 109/2025/QH15 (5 bậc, giảm trừ 15,5 triệu + 6,2 triệu/người phụ thuộc) — kèm Python API có test |
| `contract-review` | Soát hợp đồng theo checklist: điều khoản bắt buộc, red flags (phạt vi phạm >8% theo Điều 418(4) BLDS, điều khoản giải quyết tranh chấp sai, …), mẫu báo cáo rủi ro cố định |
| `labor-law` | Bảng tra nhanh Luật lao động 2025 (44/2025/QH15): thử việc, giờ làm, làm thêm, nghỉ phép, báo trước khi chấm dứt |

Điểm khác biệt: **mọi con số pháp lý đều dẫn chiếu đến luật/thông tư cụ
thể**, và workflow buộc agent phải kiểm tra văn bản hợp nhất trước khi trích
số điều. Hai skill tính toán đi kèm script Python **đã có test** — agent
chạy script thay vì tự nhớ lại quy tắc.

> Các skill phản ánh quy định tại thời điểm **tháng 11/2026**. Thuế và hóa
> đơn VN thay đổi theo thông tư — hãy đối chiếu lại hiệu lực trước khi dùng
> trong hệ thống thật.

### Cài đặt

```bash
# Claude Code
cp -r skills/* ~/.claude/skills/
# Codex
cp -r skills/* ~/.codex/skills/
```

### Chạy thử

```bash
python skills/e-invoice/scripts/validate_hd.py hoa_don_sample.xml
python skills/payroll-tax/scripts/payroll.py \
    --gross 25000000 --month 2026-08 --dependents 1
```

### Test

Không cần thư viện ngoài:

```bash
python skills/e-invoice/scripts/test_validate_hd.py
python skills/payroll-tax/scripts/test_payroll.py
```

### Miễn trừ

Bộ skill này là tài liệu tham khảo và công cụ tự động hóa, **không phải tư
văn pháp lý**. Mọi quyết định ký hợp đồng / khai thuế phải có luật sư xác
nhận.
