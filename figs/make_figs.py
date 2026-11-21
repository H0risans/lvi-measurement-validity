# -*- coding: utf-8 -*-
"""Generate schematic/data figures for the small paper as SVG (no matplotlib).

Figures:
  fig1_pipeline.svg  -- event-level injection + exposure verification flow
  fig2_support.svg   -- effective inlier count around the replay window
  fig3_output_hold.svg -- published envelope: output hold vs no hold (log scale)
"""
import csv
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PULL = os.path.join(ROOT, "第4-5章_判别与恢复", "f_stage", "pull")

FONT = "Arial, Helvetica, sans-serif"
INK = "#1f2933"
MUTED = "#6b7280"
GRID = "#e5e7eb"
RED = "#c0392b"
BLUE = "#2c6fbb"
GRAY = "#8a8f98"
ORANGE = "#d97706"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def svg_open(w, h):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
        f'<g font-family="{FONT}" fill="{INK}">',
    ]


def svg_close():
    return ["</g>", "</svg>"]


def rect(x, y, w, h, fill="#ffffff", stroke=INK, sw=1.4, rx=6, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def line(x1, y1, x2, y2, stroke=INK, sw=1.2, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}/>')


def text(x, y, s, size=14, fill=INK, weight="normal", anchor="middle"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{esc(s)}</text>')


def path(points, stroke=INK, sw=2.0, fill="none"):
    if not points:
        return ""
    d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>'


def arrow(x1, y1, x2, y2, stroke=INK, sw=1.6):
    # simple arrow with a small head
    ang = math.atan2(y2 - y1, x2 - x1)
    h = 8
    a1 = ang + math.radians(155)
    a2 = ang - math.radians(155)
    p1 = (x2 + h * math.cos(a1), y2 + h * math.sin(a1))
    p2 = (x2 + h * math.cos(a2), y2 + h * math.sin(a2))
    return (line(x1, y1, x2, y2, stroke, sw) +
            f'<path d="M {x2:.1f},{y2:.1f} L {p1[0]:.1f},{p1[1]:.1f} L {p2[0]:.1f},{p2[1]:.1f} Z" fill="{stroke}"/>')


def read_series(tag):
    p = os.path.join(PULL, tag, "safety_risk.csv")
    rows = []
    with open(p, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                t = float(r["t_vio"])
                n = float(r["n_eff_pts"])
            except (KeyError, ValueError):
                continue
            rows.append((t, n))
    rows.sort()
    return rows


def fig1():
    w, h = 980, 360
    out = svg_open(w, h)
    out.append(text(30, 34, "Figure 1. Event-level injection and processing-exposure verification", 18, INK, "bold", "start"))
    boxes = [
        (30, 90, 150, 76, "Input stream\n40 Hz images"),
        (230, 90, 170, 76, "Injector\ndrop / saturation / replay"),
        (450, 90, 170, 76, "Estimator\n10 Hz visual updates"),
        (660, 90, 170, 76, "Two-stage decision\nOK / degraded / unavailable"),
        (850, 90, 100, 76, "Output\nhold optional"),
    ]
    for x, y, bw, bh, label in boxes:
        out.append(rect(x, y, bw, bh, "#f8fafc"))
        lines = label.split("\n")
        out.append(text(x + bw / 2, y + 32, lines[0], 14, INK, "bold"))
        if len(lines) > 1:
            out.append(text(x + bw / 2, y + 54, lines[1], 12.5, MUTED))
    for i in range(len(boxes) - 1):
        x1 = boxes[i][0] + boxes[i][2]
        x2 = boxes[i + 1][0]
        out.append(arrow(x1 + 4, 128, x2 - 4, 128))
    # evidence row
    out.append(text(30, 226, "Per-event evidence", 14, INK, "bold", "start"))
    ev = [
        (30, 246, 230, 66, "Event table\naction / content age / window"),
        (290, 246, 230, 66, "Processing exposure\nimage log × visual-update log"),
        (550, 246, 250, 66, "Trajectory metrics\nAPE / RPE / null distribution"),
        (830, 246, 120, 66, "Decision\nindependent of indicators"),
    ]
    for x, y, bw, bh, label in ev:
        out.append(rect(x, y, bw, bh, "#fffdf5", ORANGE, 1.4, 4, "5,4"))
        lines = label.split("\n")
        out.append(text(x + bw / 2, y + 27, lines[0], 13, INK, "bold"))
        if len(lines) > 1:
            out.append(text(x + bw / 2, y + 48, lines[1], 11.5, MUTED))
    # dashed links from pipeline to evidence
    out.append(line(305, 166, 145, 246, ORANGE, 1.2, "4,4"))
    out.append(line(525, 166, 405, 246, ORANGE, 1.2, "4,4"))
    out.append(line(735, 166, 675, 246, ORANGE, 1.2, "4,4"))
    out.append(text(490, 336, "A measurable content-anomaly effect requires both: the event reached the estimator, and the trajectory changed beyond the run-to-run null distribution.",
                    12.5, MUTED, "normal", "middle"))
    out += svg_close()
    return "\n".join(out)


def fig2():
    w, h = 980, 460
    out = svg_open(w, h)
    out.append(text(30, 32, "Figure 2. Valid inlier count inside the content-replay window", 18, INK, "bold", "start"))
    panels = [("exp14", "Sequence 14 (3 s / 6 s)", 70, 80, 390, 300),
              ("exp18", "Sequence 18 (3 s / 6 s)", 540, 80, 390, 300)]
    series = {
        "exp14": [("f_exp14_R3_r1", RED, "3 s"), ("f_exp14_R6_r1", BLUE, "6 s")],
        "exp18": [("f_exp18_R3_r1", RED, "3 s"), ("f_exp18_R6_r1", BLUE, "6 s")],
    }
    for key, title, ox, oy, pw, ph in panels:
        xmin, xmax = 27.0, 40.0
        ymax = 120.0
        out.append(text(ox + pw / 2, oy - 16, title, 14, INK, "bold"))
        # axes
        out.append(line(ox, oy, ox, oy + ph, INK, 1.2))
        out.append(line(ox, oy + ph, ox + pw, oy + ph, INK, 1.2))
        # window shading
        xw1 = ox + (30 - xmin) / (xmax - xmin) * pw
        xw2 = ox + (32 - xmin) / (xmax - xmin) * pw
        out.append(f'<rect x="{xw1:.1f}" y="{oy}" width="{xw2 - xw1:.1f}" height="{ph}" fill="#fde8e8" opacity="0.7"/>')
        # y grid
        for v in (0, 30, 60, 90, 120):
            y = oy + ph - v / ymax * ph
            out.append(line(ox, y, ox + pw, y, GRID, 1.0))
            out.append(text(ox - 8, y + 4, str(v), 11, MUTED, "normal", "end"))
        # x ticks
        for t in (27, 30, 32, 35, 38, 40):
            x = ox + (t - xmin) / (xmax - xmin) * pw
            out.append(line(x, oy + ph, x, oy + ph + 5, INK, 1.0))
            out.append(text(x, oy + ph + 20, str(t), 11, MUTED))
        out.append(text(ox + pw / 2, oy + ph + 42, "Time (s)", 12, MUTED))
        # data + baseline band
        for tag, color, lab in series[key]:
            rows = read_series(tag)
            base = [n for t, n in rows if (t < 29.0 or t > 33.0)]
            base.sort()
            if base:
                q1 = base[len(base) // 4]
                q3 = base[len(base) * 3 // 4]
                y1 = oy + ph - min(q1, ymax) / ymax * ph
                y2 = oy + ph - min(q3, ymax) / ymax * ph
                out.append(f'<rect x="{ox}" y="{y2:.1f}" width="{pw}" height="{max(1, y1 - y2):.1f}" '
                           f'fill="{color}" opacity="0.06"/>')
            pts = [(ox + (t - xmin) / (xmax - xmin) * pw,
                    oy + ph - min(n, ymax) / ymax * ph)
                   for t, n in rows if xmin <= t <= xmax]
            out.append(path(pts, color, 1.8))
        # legend
        lx = ox + 12
        for i, (tag, color, lab) in enumerate(series[key]):
            yy = oy + 18 + i * 20
            out.append(line(lx, yy - 4, lx + 22, yy - 4, color, 2.4))
            out.append(text(lx + 28, yy, lab, 12, INK, "normal", "start"))
        out.append(text(ox + 12, oy + 76, "shaded = [30,32) s", 11, MUTED, "normal", "start"))
    out.append(text(70, 434, "Vertical axis: valid inlier count; light band: interquartile range outside the window.", 12, MUTED, "normal", "start"))
    out += svg_close()
    return "\n".join(out)


def fig3():
    w, h = 760, 420
    out = svg_open(w, h)
    out.append(text(30, 32, "Figure 3. Published-pose envelope before and after output hold", 18, INK, "bold", "start"))
    vals = [
        ("A strict hold\nmedian threshold", [5.280, 5.295], "#2e7d32"),
        ("B relaxed hold\n960 points", [5.306, 5.303], "#f9a825"),
        ("C no hold\nsame median threshold", [71757.19, 32342.96], "#c62828"),
    ]
    x0, y0, pw, ph = 90, 70, 620, 280
    ymin_log, ymax_log = 0.0, 5.0  # 1 .. 1e5
    out.append(line(x0, y0, x0, y0 + ph, INK, 1.2))
    out.append(line(x0, y0 + ph, x0 + pw, y0 + ph, INK, 1.2))
    for e in range(0, 6):
        y = y0 + ph - (e - ymin_log) / (ymax_log - ymin_log) * ph
        out.append(line(x0, y, x0 + pw, y, GRID, 1.0))
        lab = "1" if e == 0 else f"10^{e}"
        out.append(text(x0 - 10, y + 4, lab, 11, MUTED, "normal", "end"))
        if e:
            out.append(text(x0 - 10, y + 4, "", 1, MUTED))
    # 50 m line
    y50 = y0 + ph - (math.log10(50) - ymin_log) / (ymax_log - ymin_log) * ph
    out.append(line(x0, y50, x0 + pw, y50, ORANGE, 1.2, "6,4"))
    out.append(text(x0 + pw - 6, y50 - 6, "50 m", 11, ORANGE, "normal", "end"))
    n = len(vals)
    slot = pw / n
    for i, (lab, vv, color) in enumerate(vals):
        cx = x0 + slot * (i + 0.5)
        bw = 42
        for j, v in enumerate(vv):
            v = max(v, 1.0)
            y = y0 + ph - (math.log10(v) - ymin_log) / (ymax_log - ymin_log) * ph
            x = cx - bw + j * (bw + 6)
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw}" height="{y0 + ph - y:.1f}" fill="{color}" opacity="0.9"/>')
            out.append(text(x + bw / 2, y - 6, f"{v:.1f}" if v < 100 else f"{v:,.0f}", 10.5, INK))
        lines = lab.split("\n")
        out.append(text(cx + 4, y0 + ph + 22, lines[0], 12.5, INK, "bold"))
        out.append(text(cx + 4, y0 + ph + 40, lines[1], 11.5, MUTED))
    out.append(text(x0 + pw / 2, y0 + ph + 70, "Maximum displacement from start (m, log scale)", 12, MUTED))
    out.append(text(30, 404, "Two repetitions per group; C crosses 50 m at 51.50 s and 57.60 s.", 11.5, MUTED, "normal", "start"))
    out += svg_close()
    return "\n".join(out)


def main():
    os.makedirs(HERE, exist_ok=True)
    for name, fn in [("fig1_pipeline.svg", fig1), ("fig2_support.svg", fig2), ("fig3_output_hold.svg", fig3)]:
        p = os.path.join(HERE, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(fn())
        print("wrote", p)


if __name__ == "__main__":
    main()
