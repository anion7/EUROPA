#!/usr/bin/env python3
"""Gantt chart for the full robotic arm mission plan from EUROPA solver."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

try:
    plt.rcParams['font.family'] = ['Noto Sans CJK JP', 'sans-serif']
except Exception:
    pass
plt.rcParams['axes.unicode_minus'] = False

# ═══ EUROPA solver result (exact times from output) ═══
phases = [
    # (name, start, end, color, subtasks)
    ("Phase1a\n大臂重启加电", 0, 980, '#78909C', [("大臂重启加电保温", 0, 980)]),
    ("Phase1b\n小臂重启加电", 25200, 25350, '#78909C', [("小臂重启加电保温", 25200, 25350)]),
    ("等待运动", 25350, 27600, '#E0E0E0', [("WaitForMotion", 25350, 27600)]),
    ("Phase2\n平台状态设置", 27600, 31130, '#42A5F5', [
        ("太阳帆板设置", 27600, 30010),
        ("舱外相机设置", 30010, 30970),
        ("禁止自主能源", 30970, 31010),
        ("禁止电源保护", 31010, 31070),
        ("禁止母线掉电", 31070, 31110),
        ("禁止热控辐射", 31110, 31130),
    ]),
    ("Phase3\n大臂运动至组合", 31130, 32970, '#66BB6A', [
        ("小臂任务前重启", 31130, 31670),
        ("大臂运动准备", 31670, 31870),
        ("转移至中间构型", 31870, 32230),
        ("大臂至舱I上方", 32230, 32670),
        ("大臂至组合构型", 32670, 32970),
    ]),
    ("Phase4\n小臂至SWA", 32970, 33740, '#FF7043', [
        ("小臂至SWA 500mm", 32970, 33340),
        ("小臂至SWA 300mm", 33340, 33740),
    ]),
    ("Phase5\n视觉捕获SWA", 33740, 34200, '#AB47BC', [
        ("视觉精定位109mm", 33740, 33900),
        ("小臂捕获SWA", 33900, 34200),
    ]),
    ("Phase6\n小臂独立设置", 34200, 35760, '#FFA726', [
        ("大臂给小臂断电", 34200, 34460),
        ("小臂SWA上电", 34460, 34860),
        ("释放转接件2(a)", 34860, 35075),
        ("视觉伺服105mm", 35075, 35215),
        ("释放转接件2(b)", 35215, 35460),
        ("小臂手爪收拢", 35460, 35760),
    ]),
]

# Comm windows
comm_windows = [
    (0, 4000, True), (4000, 22000, False),
    (22000, 26200, True), (26200, 27600, False),
    (27600, 46000, True), (46000, 49000, False),
    (49000, 55000, True),
]

# SWA occlusion
occ_windows = [
    (0, 40000, False), (40000, 40400, True), (40400, 55000, False),
]

# ═══ Plot ═══
fig, axes = plt.subplots(3, 1, figsize=(20, 12), sharex=True,
                          gridspec_kw={'height_ratios': [8, 1.0, 1.0]})
fig.suptitle('空间站机械臂全任务规划甘特图 (EUROPA Solver)', fontsize=16, fontweight='bold')

ax = axes[0]
y_pos = len(phases)
phase_colors = []

for idx, (phase_name, ps, pe, color, subtasks) in enumerate(phases):
    y = y_pos - idx
    # Phase bar (background)
    ax.barh(y, pe - ps, left=ps, height=0.7, color=color, alpha=0.3, edgecolor=color, lw=1.5)

    # Sub-task bars
    for si, (sname, ss, se) in enumerate(subtasks):
        shade = 0.6 + 0.3 * (si % 2)
        ax.barh(y, se - ss, left=ss, height=0.5, color=color, alpha=shade,
                edgecolor='white', lw=0.5)
        if se - ss > 300:
            ax.text((ss + se) / 2, y, sname, ha='center', va='center',
                    fontsize=5.5, color='white', fontweight='bold')

    # Phase label
    ax.text(ps - 200, y, phase_name, ha='right', va='center', fontsize=7.5, fontweight='bold')

ax.set_yticks([])
ax.set_ylim(0, y_pos + 1.5)
ax.set_ylabel('任务阶段', fontsize=12)
ax.grid(axis='x', alpha=0.3, ls='--')

# Mark SWA-sensitive phases
for idx, (_, ps, pe, _, _) in enumerate(phases):
    y = y_pos - idx
    name = phases[idx][0]
    if 'Phase4' in name or 'Phase5' in name:
        ax.annotate('⚠ SWA', xy=(pe + 100, y), fontsize=7, color='red', fontweight='bold')

# Legend
legend_items = [
    mpatches.Patch(fc='#78909C', alpha=0.7, label='Phase1: 重启加电'),
    mpatches.Patch(fc='#42A5F5', alpha=0.7, label='Phase2: 平台设置 (3530s)'),
    mpatches.Patch(fc='#66BB6A', alpha=0.7, label='Phase3: 大臂至组合 (1840s)'),
    mpatches.Patch(fc='#FF7043', alpha=0.7, label='Phase4: 小臂至SWA (770s) ⚠遮挡'),
    mpatches.Patch(fc='#AB47BC', alpha=0.7, label='Phase5: 视觉捕获 (460s) ⚠遮挡'),
    mpatches.Patch(fc='#FFA726', alpha=0.7, label='Phase6: 独立设置 (1560s)'),
]
ax.legend(handles=legend_items, loc='upper left', fontsize=8, framealpha=0.9, ncol=2)

# ─── Comm windows ───
ax2 = axes[1]
ax2.set_ylabel('通信窗口', fontsize=10)
for ts, te, is_on in comm_windows:
    c = '#4CAF50' if is_on else '#EF9A9A'
    a = 0.6 if is_on else 0.3
    ax2.barh(0.5, te - ts, left=ts, height=0.6, color=c, ec='gray', lw=0.5, alpha=a)
    if is_on and te - ts > 2000:
        ax2.text((ts + te) / 2, 0.5, f'通信[{ts},{te}]', ha='center', va='center',
                 fontsize=6, color='white', fontweight='bold')
ax2.set_yticks([0.5])
ax2.set_yticklabels(['CommWindow'], fontsize=9)
ax2.set_ylim(0, 1)
ax2.grid(axis='x', alpha=0.3, ls='--')

# ─── SWA occlusion ───
ax3 = axes[2]
ax3.set_ylabel('SWA遮挡', fontsize=10)
ax3.set_xlabel('时间 (s)', fontsize=12)
for ts, te, is_active in occ_windows:
    c = '#F44336' if is_active else '#C8E6C9'
    a = 0.7 if is_active else 0.2
    ax3.barh(0.5, te - ts, left=ts, height=0.6, color=c, ec='gray', lw=0.5, alpha=a)
    if is_active:
        ax3.text((ts + te) / 2, 0.5, f'遮挡[{ts},{te}]', ha='center', va='center',
                 fontsize=6, color='white', fontweight='bold')
ax3.set_yticks([0.5])
ax3.set_yticklabels(['OcclusionSWA'], fontsize=9)
ax3.set_ylim(0, 1)
ax3.grid(axis='x', alpha=0.3, ls='--')

ax3.set_xlim(-2000, 40000)
plt.tight_layout()

save_path = '/opt/cursor/artifacts/arm_mission_gantt.png'
plt.savefig(save_path, dpi=150, bbox_inches='tight')
plt.savefig('/workspace/examples/ArmMission/arm_mission_gantt.png', dpi=150, bbox_inches='tight')
print(f"Saved: {save_path}")
