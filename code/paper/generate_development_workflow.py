"""Generate a Chinese development-only evidence-flow diagram.

This diagram records workflow state rather than a performance conclusion.  It is
deliberately written outside paper/figures because Q3's final human gate and
Secondary pressure test have not completed.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "development_figures"
PNG = OUT / "evidence_workflow_development.png"
SVG = OUT / "evidence_workflow_development.svg"
LOG = OUT / "render_check.json"


def box(ax, xy, text, color, *, dashed=False):
    x, y, w, h = xy
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.025",
        linewidth=1.35,
        edgecolor=color,
        facecolor="#FFFFFF",
        linestyle="--" if dashed else "-",
        zorder=2,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10,
            color="#202020", linespacing=1.45, zorder=3)
    return (x, y, w, h)


def arrow(ax, a, b, *, color="#6B7280", label=None):
    xa, ya, wa, ha = a
    xb, yb, wb, hb = b
    start = (xa + wa, ya + ha / 2)
    end = (xb, yb + hb / 2)
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=15,
                                 linewidth=1.25, color=color, zorder=1))
    if label:
        ax.text((start[0] + end[0]) / 2, max(start[1], end[1]) + 0.05, label,
                ha="center", va="bottom", fontsize=8.5, color="#4B5563")


def render_check(fig):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    canvas = fig.bbox
    issues = []
    for text in fig.findobj(match=plt.Text):
        if not text.get_text():
            continue
        if text.get_fontsize() < 6.5:
            issues.append({"kind": "small_font", "text": text.get_text(), "size": text.get_fontsize()})
        bbox = text.get_window_extent(renderer=renderer)
        if not (canvas.contains(bbox.x0, bbox.y0) and canvas.contains(bbox.x1, bbox.y1)):
            issues.append({"kind": "text_out_of_canvas", "text": text.get_text()})
    return issues


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "svg.fonttype": "none",
        "font.size": 10,
    })
    fig, ax = plt.subplots(figsize=(13, 5.6))
    fig.patch.set_facecolor("#FAFBFC")
    ax.set_xlim(0, 14.6)
    ax.set_ylim(0, 7)
    ax.axis("off")

    q1 = box(ax, (0.45, 3.65, 2.25, 1.25), "P0 / Q1\n124 枚电芯的审计与描述", "#2563EB")
    q2 = box(ax, (3.45, 3.65, 2.45, 1.25), "Q2\n策略—寿命关联与可信域", "#2563EB")
    k5 = box(ax, (6.7, 4.65, 2.45, 1.25), "Q3：M3R-k=5\n早期曲线增强筛查候选", "#D97706")
    k100 = box(ax, (6.7, 2.25, 2.45, 1.25), "Q3：M2-k=100\n开发集最低误差校正候选", "#2563EB")
    q4 = box(ax, (9.95, 3.65, 2.55, 1.25), "Q4\n已有策略的开发池比较\n新策略仅 provisional", "#7C3AED")
    sec = box(ax, (9.95, 1.25, 2.55, 1.25), "最终外部压力测试\nSecondary（尚未读取）", "#DC2626", dashed=True)
    end = box(ax, (13.0, 3.65, 1.05, 1.25), "待冻结\n交付", "#6B7280", dashed=True)

    arrow(ax, q1, q2)
    arrow(ax, q2, k5)
    arrow(ax, q2, k100)
    arrow(ax, k5, q4)
    arrow(ax, k100, q4)
    arrow(ax, q4, end)
    arrow(ax, sec, end, color="#DC2626")
    ax.text(13.52, 3.25, "等待 Q3 人工闸门\n与 Secondary 压力测试", ha="center", va="top",
            fontsize=8.3, color="#6B7280", linespacing=1.4)

    ax.text(0.45, 6.55, "证据流程（开发版，非最终推荐）", fontsize=15, fontweight="bold", color="#111827")
    ax.text(0.45, 6.08,
            "图仅说明当前数据流与验证边界：Q3 的稳定性人工裁决和 Secondary 压力测试尚未完成，不能据此输出最终策略。",
            fontsize=9.5, color="#4B5563")
    ax.text(0.45, 0.35,
            "数据来源：P0 深层审计；Q2 Round 1；Q3 Round 2/3；Q4 existing-policy Round 2。",
            fontsize=8.5, color="#6B7280")

    fig.savefig(SVG, bbox_inches="tight")
    fig.savefig(PNG, dpi=300, bbox_inches="tight")
    issues = render_check(fig)
    LOG.write_text(json.dumps({"figure": str(PNG), "passed": not issues, "issues": issues}, ensure_ascii=False, indent=2), encoding="utf-8")
    plt.close(fig)
    if issues:
        raise RuntimeError(f"render check failed: {issues}")


if __name__ == "__main__":
    main()
