"""Render the measured batch distributions from docs/benchmarks/{v1,v2}.json."""

import json
from pathlib import Path
from statistics import median

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D


DATA = Path(__file__).resolve().parents[1] / "docs" / "benchmarks"


def read_measurements():
    v1 = json.loads((DATA / "v1.json").read_text(encoding="utf-8"))
    v2 = json.loads((DATA / "v2.json").read_text(encoding="utf-8"))
    points = {}
    scenarios = {"first": "首条含握手", "one_way": "同向连发", "alternating": "轮流回复",
                 "same": "同向连发", "alternate": "轮流回复"}
    for row in v1["results"]:
        if row["text_bytes"] == 128 and row["mode"] in ("v1_classical", "v1_hybrid"):
            mode = "经典" if row["mode"] == "v1_classical" else "混合"
            points["v1", scenarios[row["scenario"]], mode] = [
                s["wall_ns"] / s["messages"] / 1e6 for s in row["samples"]
            ]
    for row in v2["batches"]:
        if row["body_bytes"] == 128 and row["mode"] in ("classic", "hybrid"):
            mode = "经典" if row["mode"] == "classic" else "混合"
            points.setdefault(("v2", scenarios[row["scenario"]], mode), []).append(row["wall_ms"] / row["count"])
    return points


def main():
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "Noto Sans CJK SC", "DejaVu Sans"]
    local_font = Path("C:/Windows/Fonts/msyh.ttc")
    if local_font.exists():
        font_manager.fontManager.addfont(local_font)
    points = read_measurements()
    colors = {"经典": "#286A9D", "混合": "#B64E24"}
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.8))
    fig.subplots_adjust(left=.08, right=.98, top=.77, bottom=.19, wspace=.25)
    fig.text(.025, .94, "ECNUchat 加密短消息的处理耗时", size=18, weight="bold", color="#233246")
    fig.text(.025, .87, "128 字节正文 · 包含发送端与接收端计算 · 单位为毫秒，对数坐标", size=11, color="#4b5664")
    for ax, client, title, limits, ticks in zip(
        axes, ["v1", "v2"], ["v1 · Python 桌面端", "v2 · JavaScript 加密核心"],
        [(.024, 3.5), (.13, 180)], [[.03, .1, .3, 1, 3], [.2, 1, 5, 20, 100]],
    ):
        ax.set_title(title, fontsize=13, loc="left", pad=12, color="#233246")
        ax.set_yscale("log")
        ax.set_ylim(*limits)
        ax.set_yticks(ticks, [str(t) for t in ticks])
        ax.minorticks_off()
        ax.grid(axis="y", color="#dce2e7", linewidth=.8)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#b4bbc2")
        ax.tick_params(length=0, pad=6, labelsize=10, colors="#4b5664")
        labels = ["首条含握手", "同向连发", "轮流回复"]
        ax.set_xlim(-.55, 2.55)
        ax.set_xticks(range(3), labels)
        for group, label in enumerate(labels):
            for offset, (mode, color) in zip([-.17, .17], colors.items()):
                values = points[client, label, mode]
                x = group + offset
                xs = [x + .014 * (i - (len(values) - 1) / 2) for i in range(len(values))]
                ax.scatter(xs, values, color=color, alpha=.45, s=19, zorder=3, linewidth=0)
                mid = median(values)
                ax.hlines(mid, x-.09, x+.09, color=color, lw=2.4, zorder=4)
                ax.annotate(f"{mid:.3g}", (x, max(values)), xytext=(0, 5),
                            textcoords="offset points", color=color, ha="center", size=9)
    handles = [Line2D([0], [0], color=c, lw=3, label=m+"模式") for m, c in colors.items()]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(.98, .99), ncol=2, frameon=False)
    fig.text(.025, .045, "圆点为各批次的平均耗时，横线和数值为批次中位数。v1 共 7 批，v2 共 8 批。", size=10, color="#4b5664")
    fig.savefig(DATA / "latency.png", dpi=160, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
