#!/usr/bin/env python3
"""
Gantt chart for the JxbMove EUROPA planning result.
Visualizes the Arm timeline, communication windows, and occlusion at base2.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

plt.rcParams['font.family'] = ['Noto Sans CJK JP', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# ── Plan data extracted from EUROPA solver output ──
# Times are [earliest_start, latest_start] ranges; we pick the earliest feasible.
# The solver gives ranges; a feasible instantiation:
#   AtBase1:            [0,  137]
#   MoveToOn900Base2:   [137, 660]  (dur=523)
#   AtOn900Base2:       [660, 690]
#   MoveToBase2:        [690, 893]  (dur=203)
#   AtBase2:            [893, 1650]
#   MoveToOn900Base3:   [1650, 2233] (dur=583)
#   AtOn900Base3:       [2233, 2436]
#   MoveToBase3:        [2436, 2639] (dur=203) -- but must end ≤2900
#   AtBase3:            [2639, 3000]

arm_tokens = [
    ("AtBase1",            0,    137,  "停驻"),
    ("MoveToOn900Base2",   137,  660,  "移动"),
    ("AtOn900Base2",       660,  690,  "停驻"),
    ("MoveToBase2",        690,  893,  "移动"),
    ("AtBase2",            893,  1650, "停驻"),
    ("MoveToOn900Base3",   1650, 2233, "移动"),
    ("AtOn900Base3",       2233, 2436, "停驻"),
    ("MoveToBase3",        2436, 2639, "移动"),
    ("AtBase3",            2639, 3000, "停驻"),
]

comm_windows = [
    ("InComms",  0,    660,  True),
    ("OutComms", 660,  690,  False),
    ("InComms",  690,  1200, True),
    ("OutComms", 1200, 1500, False),
    ("InComms",  1500, 2900, True),
]

occlusion = [
    ("Inactive", 0,    690,  False),
    ("Active",   690,  720,  True),
    ("Inactive", 720,  1500, False),
    ("Active",   1500, 1650, True),
    ("Inactive", 1650, 3000, False),
]

# Location names for y-axis labels
loc_names = {
    "AtBase1":          "base1",
    "AtOn900Base2":     "on_900_base2",
    "AtBase2":          "base2",
    "AtOn900Base3":     "on_900_base3",
    "AtBase3":          "base3",
}

# ── Plot ──
fig, axes = plt.subplots(3, 1, figsize=(16, 9), sharex=True,
                          gridspec_kw={'height_ratios': [5, 1.2, 1.2]})
fig.suptitle('JxbMove 规划结果甘特图  (EUROPA Solver)', fontsize=16, fontweight='bold')

# ---- Arm timeline (top) ----
ax = axes[0]
ax.set_ylabel('机械臂位置', fontsize=12)

y_positions = {
    "base1": 5,
    "on_900_base2": 4,
    "base2": 3,
    "on_900_base3": 2,
    "base3": 1,
}

# Draw stopped (At) tokens
for name, t_start, t_end, kind in arm_tokens:
    if kind == "停驻":
        loc = loc_names[name]
        y = y_positions[loc]
        width = t_end - t_start
        bar = ax.barh(y, width, left=t_start, height=0.5, color='#4CAF50',
                       edgecolor='#2E7D32', linewidth=1.2, alpha=0.85)
        if width > 80:
            ax.text(t_start + width/2, y, f'{name}\n[{t_start},{t_end}]',
                    ha='center', va='center', fontsize=7, fontweight='bold', color='white')

# Draw move tokens as arrows between locations
move_colors = {'MoveToOn900Base2': '#2196F3', 'MoveToBase2': '#FF9800',
               'MoveToOn900Base3': '#9C27B0', 'MoveToBase3': '#F44336'}

for name, t_start, t_end, kind in arm_tokens:
    if kind == "移动":
        # Determine from/to y positions
        if name == "MoveToOn900Base2":
            y_from, y_to = y_positions["base1"], y_positions["on_900_base2"]
        elif name == "MoveToBase2":
            y_from, y_to = y_positions["on_900_base2"], y_positions["base2"]
        elif name == "MoveToOn900Base3":
            y_from, y_to = y_positions["base2"], y_positions["on_900_base3"]
        elif name == "MoveToBase3":
            y_from, y_to = y_positions["on_900_base3"], y_positions["base3"]

        color = move_colors[name]
        dur = t_end - t_start

        # Draw a diagonal arrow representing movement
        ax.annotate('', xy=(t_end, y_to), xytext=(t_start, y_from),
                    arrowprops=dict(arrowstyle='->', color=color, lw=2.5))
        # Label
        mid_t = (t_start + t_end) / 2
        mid_y = (y_from + y_to) / 2
        ax.text(mid_t, mid_y + 0.3, f'{dur}s',
                ha='center', va='bottom', fontsize=9, fontweight='bold',
                color=color,
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=color, alpha=0.9))

ax.set_yticks(list(y_positions.values()))
ax.set_yticklabels(list(y_positions.keys()), fontsize=10)
ax.set_ylim(0.3, 5.8)
ax.grid(axis='x', alpha=0.3, linestyle='--')

# ---- Communication windows (middle) ----
ax2 = axes[1]
ax2.set_ylabel('通信窗口', fontsize=11)
for name, t_start, t_end, is_on in comm_windows:
    color = '#4CAF50' if is_on else '#F44336'
    alpha = 0.7 if is_on else 0.4
    ax2.barh(0.5, t_end - t_start, left=t_start, height=0.6,
             color=color, edgecolor='gray', linewidth=0.5, alpha=alpha)
    if t_end - t_start > 60:
        label = "通信" if is_on else "中断"
        ax2.text((t_start + t_end)/2, 0.5, f'{label}\n[{t_start},{t_end}]',
                 ha='center', va='center', fontsize=7, color='white', fontweight='bold')
ax2.set_yticks([0.5])
ax2.set_yticklabels(['CommWindow'], fontsize=10)
ax2.set_ylim(0, 1.0)
ax2.grid(axis='x', alpha=0.3, linestyle='--')

# ---- Occlusion at base2 (bottom) ----
ax3 = axes[2]
ax3.set_ylabel('base2 遮挡', fontsize=11)
ax3.set_xlabel('时间 (s)', fontsize=12)
for name, t_start, t_end, is_active in occlusion:
    color = '#F44336' if is_active else '#81C784'
    alpha = 0.7 if is_active else 0.3
    ax3.barh(0.5, t_end - t_start, left=t_start, height=0.6,
             color=color, edgecolor='gray', linewidth=0.5, alpha=alpha)
    if is_active:
        ax3.text((t_start + t_end)/2, 0.5, f'遮挡\n[{t_start},{t_end}]',
                 ha='center', va='center', fontsize=7, color='white', fontweight='bold')
ax3.set_yticks([0.5])
ax3.set_yticklabels(['OcclusionBase2'], fontsize=10)
ax3.set_ylim(0, 1.0)
ax3.grid(axis='x', alpha=0.3, linestyle='--')

# ---- Common x-axis ----
ax3.set_xlim(-50, 3100)
ax3.set_xticks(np.arange(0, 3100, 200))

# ---- Legend ----
legend_elements = [
    mpatches.Patch(facecolor='#4CAF50', edgecolor='#2E7D32', label='停驻 (At)'),
    mpatches.FancyArrow(0, 0, 1, 0, width=0.3, color='#2196F3', label='移动 (Move)'),
    mpatches.Patch(facecolor='#4CAF50', alpha=0.7, label='通信可用'),
    mpatches.Patch(facecolor='#F44336', alpha=0.4, label='通信中断'),
    mpatches.Patch(facecolor='#F44336', alpha=0.7, label='遮挡活跃'),
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=9, framealpha=0.9)

plt.tight_layout()
plt.savefig('/opt/cursor/artifacts/jxb_gantt_chart.png', dpi=150, bbox_inches='tight')
plt.savefig('/workspace/examples/JxbMove/jxb_gantt_chart.png', dpi=150, bbox_inches='tight')
print("Gantt chart saved.")
