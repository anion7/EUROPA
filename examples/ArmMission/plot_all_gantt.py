#!/usr/bin/env python3
"""
Generate four publication-quality Gantt charts for the ArmMission:
  1. Communication windows & SWA occlusion
  2. Per-phase sub-task Gantt (6 separate phase panels)
  3. Overall mission Gantt with inset zoom panels
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
from matplotlib.gridspec import GridSpec
import numpy as np

try:
    plt.rcParams['font.family'] = ['Noto Sans CJK JP', 'sans-serif']
except Exception:
    pass
plt.rcParams['axes.unicode_minus'] = False

# ════════════════════════════════════════════════════════
# DATA
# ════════════════════════════════════════════════════════
comm_windows = [
    (0, 4000, True), (4000, 22000, False),
    (22000, 26200, True), (26200, 27600, False),
    (27600, 46000, True), (46000, 49000, False),
    (49000, 55000, True),
]

occ_windows = [
    (0, 40000, False), (40000, 40400, True), (40400, 55000, False),
]

phase_colors = {
    1: '#78909C', 2: '#42A5F5', 3: '#66BB6A',
    4: '#FF7043', 5: '#AB47BC', 6: '#FFA726',
}

sub_tasks = {
    1: [("大臂重启加电保温", 0, 980),
        ("小臂重启加电保温", 25200, 25350)],
    2: [("太阳帆板设置", 27600, 30010),
        ("舱外相机设置", 30010, 30970),
        ("禁止自主能源", 30970, 31010),
        ("禁止电源保护", 31010, 31070),
        ("禁止母线掉电", 31070, 31110),
        ("禁止热控辐射", 31110, 31130)],
    3: [("小臂任务前重启", 31130, 31670),
        ("大臂运动准备", 31670, 31870),
        ("转移至中间构型", 31870, 32230),
        ("大臂至舱I上方", 32230, 32670),
        ("大臂至组合构型", 32670, 32970)],
    4: [("小臂至SWA 500mm", 32970, 33340),
        ("小臂至SWA 300mm", 33340, 33740)],
    5: [("视觉精定位109mm", 33740, 33900),
        ("小臂捕获SWA", 33900, 34200)],
    6: [("大臂给小臂断电", 34200, 34460),
        ("小臂SWA上电", 34460, 34860),
        ("释放转接件(a)", 34860, 35075),
        ("视觉伺服105mm", 35075, 35215),
        ("释放转接件(b)", 35215, 35460),
        ("小臂手爪收拢", 35460, 35760)],
}

phase_names = {
    1: "Phase1: 重启加电", 2: "Phase2: 平台设置",
    3: "Phase3: 大臂至组合", 4: "Phase4: 小臂至SWA",
    5: "Phase5: 视觉捕获", 6: "Phase6: 独立设置",
}

phase_ranges = {
    1: (0, 25350), 2: (27600, 31130), 3: (31130, 32970),
    4: (32970, 33740), 5: (33740, 34200), 6: (34200, 35760),
}

# ════════════════════════════════════════════════════════
# CHART 1: Communication Windows & Occlusion
# ════════════════════════════════════════════════════════
def plot_comm_occ():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 4.5), sharex=True,
                                     gridspec_kw={'height_ratios': [1, 1]})
    fig.suptitle('通信窗口与SWA遮挡状态时间线', fontsize=14, fontweight='bold')

    # Comm
    for ts, te, on in comm_windows:
        c = '#4CAF50' if on else '#EF9A9A'
        a = 0.75 if on else 0.35
        ax1.barh(0.5, te-ts, left=ts, height=0.6, color=c, ec='gray', lw=0.5, alpha=a)
        label = "通信可用" if on else "通信中断"
        if te - ts > 1500:
            ax1.text((ts+te)/2, 0.5, f'{label}\n[{ts}, {te}]',
                     ha='center', va='center', fontsize=7, color='white', fontweight='bold')
    ax1.set_ylabel('通信窗口', fontsize=11)
    ax1.set_yticks([0.5]); ax1.set_yticklabels(['CommWindow'], fontsize=9)
    ax1.set_ylim(0, 1); ax1.grid(axis='x', alpha=0.3, ls='--')
    ax1.legend(handles=[
        mpatches.Patch(fc='#4CAF50', alpha=0.75, label='通信可用 (InComms)'),
        mpatches.Patch(fc='#EF9A9A', alpha=0.35, label='通信中断 (OutComms)'),
    ], loc='upper right', fontsize=8)

    # Occlusion
    for ts, te, act in occ_windows:
        c = '#F44336' if act else '#C8E6C9'
        a = 0.8 if act else 0.25
        ax2.barh(0.5, te-ts, left=ts, height=0.6, color=c, ec='gray', lw=0.5, alpha=a)
        if act:
            ax2.text((ts+te)/2, 0.5, f'遮挡活跃\n[{ts},{te}]',
                     ha='center', va='center', fontsize=7, color='white', fontweight='bold')
    ax2.set_ylabel('SWA遮挡', fontsize=11)
    ax2.set_xlabel('时间 (s)', fontsize=11)
    ax2.set_yticks([0.5]); ax2.set_yticklabels(['OcclusionSWA'], fontsize=9)
    ax2.set_ylim(0, 1); ax2.grid(axis='x', alpha=0.3, ls='--')
    ax2.legend(handles=[
        mpatches.Patch(fc='#F44336', alpha=0.8, label='遮挡活跃 (Active)'),
        mpatches.Patch(fc='#C8E6C9', alpha=0.25, label='遮挡不活跃 (Inactive)'),
    ], loc='upper right', fontsize=8)
    ax2.set_xlim(-500, 56000)

    plt.tight_layout()
    plt.savefig('/opt/cursor/artifacts/gantt_1_comm_occ.png', dpi=200, bbox_inches='tight')
    plt.savefig('/workspace/examples/ArmMission/gantt_1_comm_occ.png', dpi=200, bbox_inches='tight')
    print("Saved: gantt_1_comm_occ.png")
    plt.close()

# ════════════════════════════════════════════════════════
# CHART 2: Per-phase sub-task panels
# ════════════════════════════════════════════════════════
def plot_per_phase():
    fig, axes = plt.subplots(6, 1, figsize=(16, 14), sharex=False)
    fig.suptitle('各阶段子任务规划结果', fontsize=14, fontweight='bold', y=0.995)

    for idx, phase_id in enumerate([1,2,3,4,5,6]):
        ax = axes[idx]
        tasks = sub_tasks[phase_id]
        color = phase_colors[phase_id]
        n = len(tasks)

        for ti, (name, ts, te) in enumerate(tasks):
            y = n - ti
            shade = 0.55 + 0.35 * (ti % 2)
            ax.barh(y, te-ts, left=ts, height=0.65, color=color, alpha=shade,
                    edgecolor='white', lw=1)
            # Label
            dur = te - ts
            if dur > 80:
                ax.text(ts + dur/2, y, f'{name} ({dur}s)',
                        ha='center', va='center', fontsize=6.5, color='white', fontweight='bold')
            else:
                ax.text(te + 20, y, f'{name} ({dur}s)',
                        ha='left', va='center', fontsize=6.5, color='#333')

        ax.set_yticks(range(1, n+1))
        ax.set_yticklabels([t[0] for t in reversed(tasks)], fontsize=7)
        ax.set_ylim(0.3, n+0.7)

        # x range: tight around phase
        all_ts = [t[1] for t in tasks]
        all_te = [t[2] for t in tasks]
        margin = max(100, (max(all_te)-min(all_ts))*0.08)
        ax.set_xlim(min(all_ts)-margin, max(all_te)+margin)
        ax.grid(axis='x', alpha=0.3, ls='--')
        ax.set_xlabel('时间 (s)', fontsize=8)

        # Phase title
        pr = phase_ranges[phase_id]
        ax.set_title(f'{phase_names[phase_id]}  [{pr[0]}s ~ {pr[1]}s]  (总时长 {pr[1]-pr[0]}s)',
                     fontsize=10, fontweight='bold', loc='left', color=color)

        # Mark SWA-sensitive
        if phase_id in [4, 5]:
            ax.text(0.98, 0.92, '⚠ SWA遮挡约束', transform=ax.transAxes,
                    ha='right', va='top', fontsize=8, color='red', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', fc='#FFF3E0', ec='red', alpha=0.9))

    plt.tight_layout()
    plt.savefig('/opt/cursor/artifacts/gantt_2_per_phase.png', dpi=200, bbox_inches='tight')
    plt.savefig('/workspace/examples/ArmMission/gantt_2_per_phase.png', dpi=200, bbox_inches='tight')
    print("Saved: gantt_2_per_phase.png")
    plt.close()

# ════════════════════════════════════════════════════════
# CHART 3: Overall mission with inset zooms
# ════════════════════════════════════════════════════════
def plot_overall_with_zoom():
    fig = plt.figure(figsize=(18, 16))
    gs = GridSpec(5, 2, figure=fig, height_ratios=[4, 1.0, 1.0, 0.3, 5],
                  hspace=0.35, wspace=0.25)

    # ── Top: overall Gantt ──
    ax_main = fig.add_subplot(gs[0, :])
    ax_comm = fig.add_subplot(gs[1, :], sharex=ax_main)
    ax_occ  = fig.add_subplot(gs[2, :], sharex=ax_main)

    fig.suptitle('空间站机械臂全任务规划甘特图 (EUROPA Solver)\n含各阶段局部放大', fontsize=15, fontweight='bold', y=0.98)

    # Main Arm timeline
    y_map = {1:6, 2:5, 3:4, 4:3, 5:2, 6:1}
    for phase_id in [1,2,3,4,5,6]:
        tasks = sub_tasks[phase_id]
        color = phase_colors[phase_id]
        y = y_map[phase_id]
        pr = phase_ranges[phase_id]

        # Phase background bar
        ax_main.barh(y, pr[1]-pr[0], left=pr[0], height=0.7, color=color, alpha=0.2,
                     edgecolor=color, lw=1.5)

        # Sub-task bars
        for ti, (name, ts, te) in enumerate(tasks):
            shade = 0.5 + 0.4 * (ti % 2)
            ax_main.barh(y, te-ts, left=ts, height=0.5, color=color, alpha=shade,
                        edgecolor='white', lw=0.5)

        # Phase label
        ax_main.text(pr[0]-300, y, phase_names[phase_id], ha='right', va='center',
                     fontsize=8, fontweight='bold', color=color)

    # WaitForMotion
    ax_main.barh(y_map[2]+0.5, 27600-25350, left=25350, height=0.3, color='#E0E0E0',
                 edgecolor='gray', lw=0.5, alpha=0.5)
    ax_main.text(26475, y_map[2]+0.5, '等待', ha='center', va='center', fontsize=6, color='gray')

    ax_main.set_yticks(list(y_map.values()))
    ax_main.set_yticklabels([phase_names[k] for k in y_map.keys()], fontsize=8)
    ax_main.set_ylim(0.2, 7)
    ax_main.grid(axis='x', alpha=0.3, ls='--')
    ax_main.set_ylabel('任务阶段', fontsize=11)

    # Legend
    legend_items = [mpatches.Patch(fc=phase_colors[k], alpha=0.7, label=phase_names[k]) for k in [1,2,3,4,5,6]]
    ax_main.legend(handles=legend_items, loc='upper left', fontsize=7, ncol=3, framealpha=0.9)

    # Comm
    for ts, te, on in comm_windows:
        c = '#4CAF50' if on else '#EF9A9A'
        a = 0.6 if on else 0.3
        ax_comm.barh(0.5, te-ts, left=ts, height=0.6, color=c, ec='gray', lw=0.5, alpha=a)
        if on and te-ts > 2000:
            ax_comm.text((ts+te)/2, 0.5, f'[{ts},{te}]', ha='center', va='center',
                         fontsize=6, color='white', fontweight='bold')
    ax_comm.set_ylabel('通信', fontsize=9)
    ax_comm.set_yticks([]); ax_comm.set_ylim(0,1)
    ax_comm.grid(axis='x', alpha=0.3, ls='--')

    # Occ
    for ts, te, act in occ_windows:
        c = '#F44336' if act else '#C8E6C9'
        a = 0.7 if act else 0.2
        ax_occ.barh(0.5, te-ts, left=ts, height=0.6, color=c, ec='gray', lw=0.5, alpha=a)
        if act:
            ax_occ.text((ts+te)/2, 0.5, f'遮挡', ha='center', va='center',
                        fontsize=6, color='white', fontweight='bold')
    ax_occ.set_ylabel('遮挡', fontsize=9)
    ax_occ.set_xlabel('时间 (s)', fontsize=10)
    ax_occ.set_yticks([]); ax_occ.set_ylim(0,1)
    ax_occ.grid(axis='x', alpha=0.3, ls='--')
    ax_occ.set_xlim(-500, 56000)

    # Draw zoom rectangles on main plot
    zoom_regions = [
        (27400, 31300, '#42A5F5', 'Phase 2-3 放大'),
        (31000, 34400, '#FF7043', 'Phase 3-5 放大'),
        (34000, 35900, '#FFA726', 'Phase 6 放大'),
    ]

    for xmin, xmax, color, label in zoom_regions:
        rect = mpatches.FancyBboxPatch((xmin, 0.3), xmax-xmin, 6.5,
                                        boxstyle="round,pad=0", fc='none',
                                        ec=color, lw=2, ls='--', alpha=0.8)
        ax_main.add_patch(rect)

    # ── Bottom: 3 zoom panels ──
    zoom_specs = [
        (0, (27400, 31300), "Phase 2~3 局部放大 [27400s ~ 31300s]", [2, 3]),
        (1, (31000, 34400), "Phase 3~5 局部放大 [31000s ~ 34400s]", [3, 4, 5]),
        (2, (34000, 35900), "Phase 6 局部放大 [34000s ~ 35900s]", [5, 6]),
    ]

    ax_zooms = []
    for col, (xmin, xmax), ztitle, phases_in in zoom_specs:
        if col < 2:
            ax_z = fig.add_subplot(gs[4, col])
        else:
            # Third panel spans remainder — use a manual position
            ax_z = fig.add_axes([0.55, 0.02, 0.42, 0.27])
        ax_zooms.append(ax_z)

        # Determine relevant phases
        relevant = [p for p in phases_in if p in sub_tasks]
        n_rows = sum(len(sub_tasks[p]) for p in relevant)

        y_cursor = n_rows
        for phase_id in relevant:
            tasks = sub_tasks[phase_id]
            color = phase_colors[phase_id]
            for ti, (name, ts, te) in enumerate(tasks):
                if ts >= xmax or te <= xmin:
                    y_cursor -= 1
                    continue
                shade = 0.5 + 0.4 * (ti % 2)
                ax_z.barh(y_cursor, te-ts, left=ts, height=0.7, color=color, alpha=shade,
                         edgecolor='white', lw=0.8)
                dur = te - ts
                mid = max(ts, xmin) + min(dur, xmax-ts)/2
                if dur > 60:
                    ax_z.text(mid, y_cursor, f'{name}\n({dur}s)',
                             ha='center', va='center', fontsize=5.5, color='white', fontweight='bold')
                else:
                    ax_z.text(te+15, y_cursor, f'{name} ({dur}s)',
                             ha='left', va='center', fontsize=5.5, color='#333')
                y_cursor -= 1

        ax_z.set_xlim(xmin, xmax)
        ax_z.set_ylim(0, n_rows + 1)
        ax_z.set_yticks([])
        ax_z.grid(axis='x', alpha=0.3, ls='--')
        ax_z.set_xlabel('时间 (s)', fontsize=8)
        ax_z.set_title(ztitle, fontsize=9, fontweight='bold', color='#333')

    plt.close()  # discard first attempt, rebuild with proper GridSpec

    # ── Rebuild with proper GridSpec ──
    fig2 = plt.figure(figsize=(18, 16))
    gs2 = GridSpec(4, 3, figure=fig2, height_ratios=[4, 1.0, 1.0, 5],
                   hspace=0.4, wspace=0.3)

    fig2.suptitle('空间站机械臂全任务规划结果甘特图 (EUROPA Solver)', fontsize=15, fontweight='bold', y=0.99)

    ax_m = fig2.add_subplot(gs2[0, :])
    ax_c = fig2.add_subplot(gs2[1, :], sharex=ax_m)
    ax_o = fig2.add_subplot(gs2[2, :], sharex=ax_m)

    # Redraw main
    for phase_id in [1,2,3,4,5,6]:
        tasks = sub_tasks[phase_id]
        color = phase_colors[phase_id]
        y = y_map[phase_id]
        pr = phase_ranges[phase_id]
        ax_m.barh(y, pr[1]-pr[0], left=pr[0], height=0.7, color=color, alpha=0.2,
                  edgecolor=color, lw=1.5)
        for ti, (name, ts, te) in enumerate(tasks):
            shade = 0.5 + 0.4*(ti%2)
            ax_m.barh(y, te-ts, left=ts, height=0.5, color=color, alpha=shade,
                     edgecolor='white', lw=0.5)
        ax_m.text(pr[0]-300, y, phase_names[phase_id], ha='right', va='center',
                  fontsize=8, fontweight='bold', color=color)

    ax_m.barh(y_map[2]+0.5, 27600-25350, left=25350, height=0.3, color='#E0E0E0',
              edgecolor='gray', lw=0.5, alpha=0.5)
    ax_m.set_yticks(list(y_map.values()))
    ax_m.set_yticklabels([phase_names[k] for k in y_map.keys()], fontsize=8)
    ax_m.set_ylim(0.2, 7); ax_m.grid(axis='x', alpha=0.3, ls='--')
    ax_m.set_ylabel('任务阶段', fontsize=11)
    ax_m.legend(handles=[mpatches.Patch(fc=phase_colors[k], alpha=0.7, label=phase_names[k]) for k in [1,2,3,4,5,6]],
                loc='upper left', fontsize=7, ncol=3, framealpha=0.9)

    # Zoom region boxes
    zoom_data = [
        ((27400, 31300), '#42A5F5', [2, 3]),
        ((31000, 34400), '#FF7043', [3, 4, 5]),
        ((34000, 35900), '#FFA726', [5, 6]),
    ]
    for (xmin, xmax), clr, _ in zoom_data:
        rect = mpatches.FancyBboxPatch((xmin, 0.3), xmax-xmin, 6.5,
                boxstyle="round,pad=0", fc='none', ec=clr, lw=2, ls='--', alpha=0.8)
        ax_m.add_patch(rect)

    # Comm
    for ts, te, on in comm_windows:
        c2 = '#4CAF50' if on else '#EF9A9A'; a2 = 0.6 if on else 0.3
        ax_c.barh(0.5, te-ts, left=ts, height=0.6, color=c2, ec='gray', lw=0.5, alpha=a2)
        if on and te-ts > 2000:
            ax_c.text((ts+te)/2, 0.5, f'[{ts},{te}]', ha='center', va='center', fontsize=6, color='white', fontweight='bold')
    ax_c.set_ylabel('通信', fontsize=9); ax_c.set_yticks([]); ax_c.set_ylim(0,1)
    ax_c.grid(axis='x', alpha=0.3, ls='--')

    # Occ
    for ts, te, act in occ_windows:
        c3 = '#F44336' if act else '#C8E6C9'; a3 = 0.7 if act else 0.2
        ax_o.barh(0.5, te-ts, left=ts, height=0.6, color=c3, ec='gray', lw=0.5, alpha=a3)
        if act:
            ax_o.text((ts+te)/2, 0.5, '遮挡', ha='center', va='center', fontsize=6, color='white', fontweight='bold')
    ax_o.set_ylabel('遮挡', fontsize=9); ax_o.set_xlabel('时间 (s)', fontsize=10)
    ax_o.set_yticks([]); ax_o.set_ylim(0,1)
    ax_o.grid(axis='x', alpha=0.3, ls='--')
    ax_o.set_xlim(-500, 56000)

    # ── Zoom panels ──
    zoom_titles = [
        "Phase 2~3 局部放大", "Phase 3~5 局部放大", "Phase 5~6 局部放大"
    ]
    for zi in range(3):
        ax_z = fig2.add_subplot(gs2[3, zi])
        (xmin, xmax), clr, phases_in = zoom_data[zi]
        relevant_tasks = []
        for pid in phases_in:
            for name, ts, te in sub_tasks[pid]:
                if te > xmin and ts < xmax:
                    relevant_tasks.append((pid, name, ts, te))

        n_rows = len(relevant_tasks)
        for ri, (pid, name, ts, te) in enumerate(relevant_tasks):
            y_r = n_rows - ri
            shade = 0.5 + 0.4*(ri%2)
            ax_z.barh(y_r, te-ts, left=ts, height=0.7, color=phase_colors[pid], alpha=shade,
                     edgecolor='white', lw=0.8)
            dur = te - ts
            if dur > (xmax-xmin)*0.05:
                ax_z.text((ts+te)/2, y_r, f'{name}\n({dur}s)', ha='center', va='center',
                         fontsize=5.5, color='white', fontweight='bold')
            else:
                ax_z.text(te+10, y_r, f'{name} ({dur}s)', ha='left', va='center',
                         fontsize=5.5, color='#333')

        ax_z.set_xlim(xmin, xmax)
        ax_z.set_ylim(0, max(n_rows+1, 2))
        ax_z.set_yticks([])
        ax_z.grid(axis='x', alpha=0.3, ls='--')
        ax_z.set_xlabel('时间 (s)', fontsize=8)
        ax_z.set_title(zoom_titles[zi], fontsize=9, fontweight='bold')
        for sp in ax_z.spines.values():
            sp.set_edgecolor(clr); sp.set_linewidth(2)

    plt.savefig('/opt/cursor/artifacts/gantt_3_overall_zoom.png', dpi=200, bbox_inches='tight')
    plt.savefig('/workspace/examples/ArmMission/gantt_3_overall_zoom.png', dpi=200, bbox_inches='tight')
    print("Saved: gantt_3_overall_zoom.png")
    plt.close()


if __name__ == '__main__':
    plot_comm_occ()
    plot_per_phase()
    plot_overall_with_zoom()
    print("All charts generated.")
