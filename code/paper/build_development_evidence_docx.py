"""Render the non-final development evidence manuscript into the supplied template.

This is intentionally a development document.  Its first page and footer-level
notice prevent it from being mistaken for the final, Secondary-validated paper.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "论文.docx"
SOURCE = ROOT / "paper" / "开发证据稿_全篇_非最终.md"
OUTPUT = ROOT / "paper" / "论文开发证据稿_非最终.docx"
MANIFEST = ROOT / "paper" / "开发证据稿构建清单.json"
FIGURES = {
    "数据审计": ROOT / "outputs" / "development_figures" / "evidence_workflow_development.png",
    "Q1": ROOT / "results" / "Q1" / "experiments" / "round1" / "figures" / "q1_01_lifetime_distribution.png",
    "Q2": ROOT / "results" / "Q2" / "experiments" / "round1" / "figures" / "m1_m2_oof_comparison.png",
    "Q3": ROOT / "results" / "Q3" / "experiments" / "round3_raw_curve_challenger" / "figures" / "q3_raw_curve_challenger.png",
    "Q4": ROOT / "results" / "Q4" / "experiments" / "existing_policy_round2_m2k100" / "figures" / "q4_existing_policy_pareto.png",
    "Q4流量": ROOT / "results" / "Q4" / "experiments" / "train_dry_run_round1" / "figures" / "q4_train_only_candidate_flow.png",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def delete_body(document: Document) -> None:
    body = document._element.body
    for element in list(body):
        if element.tag != qn("w:sectPr"):
            body.remove(element)


def style_run(run, size: float = 10.5, bold: bool = False) -> None:
    run.font.name = "宋体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(size)
    run.bold = bold


def clean_markup(text: str) -> str:
    """Keep the DOCX readable when the traceable source uses Markdown/TeX inline marks."""
    replacements = {
        "**": "",
        "$": "",
        "\\\\ln": "ln",
        "\\\\Delta": "Δ",
        "\\\\ge": "≥",
        "\\\\%": "%",
        "C_1": "C₁",
        "C_2": "C₂",
        "L_i": "Lᵢ",
        "z_i": "zᵢ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def add_paragraph(document: Document, text: str, *, centered: bool = False, bold: bool = False, size: float = 10.5) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.first_line_indent = Pt(21) if not centered else Pt(0)
    paragraph.paragraph_format.line_spacing = 1.35
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if centered else WD_ALIGN_PARAGRAPH.JUSTIFY
    style_run(paragraph.add_run(clean_markup(text)), size=size, bold=bold)


def add_heading(document: Document, text: str, level: int) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(10 if level == 1 else 7)
    paragraph.paragraph_format.space_after = Pt(5)
    run = paragraph.add_run(clean_markup(text))
    run.font.name = "黑体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    run.font.size = Pt(14 if level == 1 else 12)
    run.bold = True


def add_formula(document: Document, latex: str) -> None:
    """Render the three verified development formulas in readable Word text.

    The source Markdown deliberately keeps LaTeX for traceability; python-docx
    has no native equation conversion, so these equivalent plain-text formulas
    avoid exposing raw TeX syntax in the handoff DOCX.
    """
    if "lVert" in latex:
        text = "min_{β₀, β} Σᵢ∈T (zᵢ − β₀ − xᵢᵀβ)² + λ‖β‖₂²"
    elif "widehat{SOH}" in latex:
        text = "ŜOHᵢ(c) = aᵢ(k) + [0.8 − aᵢ(k)] · [G(min{c/L̂ᵢ,1}) − G(k/L̂ᵢ)] / [0.8 − G(k/L̂ᵢ)]"
    elif "tau_" in latex:
        text = "τ₀–₈₀ = 60 · [q/C₁ + (0.8 − q)/C₂ᵉᶠᶠ] min"
    else:
        text = clean_markup(latex)
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(3)
    paragraph.paragraph_format.space_after = Pt(5)
    style_run(paragraph.add_run(text), size=10.5)


def parse_table(lines: list[str]) -> list[list[str]]:
    rows = []
    for line in lines:
        if re.fullmatch(r"\|[\s:|\-]+\|", line):
            continue
        rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


def add_table(document: Document, rows: list[list[str]]) -> None:
    if not rows:
        return
    table = document.add_table(rows=len(rows), cols=len(rows[0]))
    table.style = "Table Grid"
    header_properties = table.rows[0]._tr.get_or_add_trPr()
    header_row = OxmlElement("w:tblHeader")
    header_row.set(qn("w:val"), "true")
    header_properties.append(header_row)
    for r, values in enumerate(rows):
        for c, value in enumerate(values):
            paragraph = table.cell(r, c).paragraphs[0]
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if r == 0 else WD_ALIGN_PARAGRAPH.LEFT
            paragraph.paragraph_format.line_spacing = 1.1
            style_run(paragraph.add_run(clean_markup(value)), size=8.5, bold=(r == 0))


def add_figure(document: Document, path: Path, caption: str) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    picture = paragraph.add_run().add_picture(str(path), width=Pt(390))
    picture._inline.docPr.set("descr", caption)
    picture._inline.docPr.set("title", caption.split("（", 1)[0])
    caption_p = document.add_paragraph()
    caption_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    style_run(caption_p.add_run(caption), size=9)


def main() -> None:
    if not TEMPLATE.exists() or not SOURCE.exists():
        raise FileNotFoundError("模板或开发证据稿不存在。")
    document = Document(TEMPLATE)
    delete_body(document)
    footer = document.sections[0].footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    style_run(footer.add_run("｜开发证据版（非最终）｜仅供论文撰写与交接使用"), size=8.5)

    add_paragraph(document, "不同 SOC 区间快充策略与电池寿命的开发期建模证据稿", centered=True, bold=True, size=18)
    add_paragraph(document, "开发证据版（非最终提交；待 Q3 裁决、Secondary 压力测试与新策略 pilot）", centered=True, size=11)
    add_paragraph(document, "说明：本稿只整理已审计、可复现的开发证据。Primary 仅作一次受限确认；所有 Q3/Q4 结论均不等同于独立外部泛化或最终最优推荐。", centered=True, size=9.5)

    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    index = 0
    figure_inserted: set[str] = set()
    while index < len(lines):
        line = lines[index].strip()
        index += 1
        if not line or line.startswith(">") or line.startswith("# "):
            continue
        if line.startswith("## "):
            heading = line[3:]
            add_heading(document, heading, 1)
            if heading.startswith("3 数据审计"):
                add_figure(document, FIGURES["数据审计"], "图 1  开发期证据流程与验证边界（非最终推荐）")
                figure_inserted.add("数据审计")
            elif heading.startswith("4 Q1"):
                add_figure(document, FIGURES["Q1"], "图 2  正式分析电芯的循环寿命分布（数据来源：Table 9 对齐结果）")
                figure_inserted.add("Q1")
            elif heading.startswith("5 Q2"):
                add_figure(document, FIGURES["Q2"], "图 3  Q2 策略分组折外预测：M1 主线与 M2 敏感性模型")
                figure_inserted.add("Q2")
            elif heading.startswith("6 Q3"):
                add_figure(document, FIGURES["Q3"], "图 4  Q3 原始电压曲线候选模型的严格仅训练集比较（非外部验证）")
                figure_inserted.add("Q3")
            elif heading.startswith("7 Q4"):
                add_figure(document, FIGURES["Q4"], "图 5  Q4 已有策略的开发池比较（非独立外部验证，非最终推荐）")
                add_figure(document, FIGURES["Q4流量"], "图 6  Q4 仅训练集候选流量与支持域诊断（不等于最优策略）")
                figure_inserted.add("Q4")
            continue
        if line == "$$":
            formula_lines = []
            while index < len(lines) and lines[index].strip() != "$$":
                formula_lines.append(lines[index].strip())
                index += 1
            if index < len(lines):
                index += 1
            add_formula(document, " ".join(formula_lines))
            continue
        if line.startswith("| "):
            table_lines = [line]
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            add_table(document, parse_table(table_lines))
            continue
        add_paragraph(document, line)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT)
    check = Document(OUTPUT)
    manifest = {
        "status": "development_evidence_docx_nonfinal",
        "template": str(TEMPLATE),
        "template_sha256": sha256(TEMPLATE),
        "source_markdown": str(SOURCE),
        "source_sha256": sha256(SOURCE),
        "output": str(OUTPUT),
        "output_sha256": sha256(OUTPUT),
        "paragraph_count": len(check.paragraphs),
        "table_count": len(check.tables),
        "figure_count": len(FIGURES),
        "final_submission_claim": False,
        "render_status": "structurally_verified; visual_render_pending_no_libreoffice",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
