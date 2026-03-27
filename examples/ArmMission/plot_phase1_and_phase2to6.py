#!/usr/bin/env python3
"""
Two publication-quality Gantt charts:
  1. Phase 1 standalone (BigArm restart + SmallArm restart over 0~27600s)
  2. Phase 2-6 combined with per-phase zoom insets (27600~36000s)
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np

try:
    plt.rcParams['font.family'] = ['Noto Sans CJK JP', 'sans-serif']
except Exception:
    pass
plt.rcParams['axes.unicode_minus'] = False

# ════════════════════════════════════════
# DATA
# ════════════════════════════════════════
comm_windows = [
    (0,4000,True),(4000,22000,False),(22000,26200,True),
    (26200,27600,False),(27600,46000,True),(46000,49000,False),(49000,55000,True),
]
occ_windows = [(0,40000,False),(40000,40400,True),(40400,55000,False)]

phase_colors = {1:'#78909C',2:'#42A5F5',3:'#66BB6A',4:'#FF7043',5:'#AB47BC',6:'#FFA726'}

sub_tasks = {
    1: [("大臂重启加电保温",0,980),("小臂重启加电保温",25200,25350)],
    2: [("太阳帆板设置",27600,30010),("舱外相机设置",30010,30970),
        ("禁止自主能源",30970,31010),("禁止电源保护",31010,31070),
        ("禁止母线掉电",31070,31110),("禁止热控辐射",31110,31130)],
    3: [("小臂任务前重启",31130,31670),("大臂运动准备",31670,31870),
        ("转移至中间构型",31870,32230),("大臂至舱I上方",32230,32670),
        ("大臂至组合构型",32670,32970)],
    4: [("小臂至SWA 500mm",32970,33340),("小臂至SWA 300mm",33340,33740)],
    5: [("视觉精定位109mm",33740,33900),("小臂捕获SWA",33900,34200)],
    6: [("大臂给小臂断电",34200,34460),("小臂SWA上电",34460,34860),
        ("释放转接件(a)",34860,35075),("视觉伺服105mm",35075,35215),
        ("释放转接件(b)",35215,35460),("小臂手爪收拢",35460,35760)],
}

phase_names = {1:"Phase1: 重启加电",2:"Phase2: 平台设置",3:"Phase3: 大臂至组合",
               4:"Phase4: 小臂至SWA",5:"Phase5: 视觉捕获",6:"Phase6: 独立设置"}

phase_ranges = {1:(0,25350),2:(27600,31130),3:(31130,32970),
                4:(32970,33740),5:(33740,34200),6:(34200,35760)}

# ════════════════════════════════════════
# CHART A: Phase 1 standalone
# ════════════════════════════════════════
def plot_phase1():
    fig, (ax_arm, ax_comm) = plt.subplots(2, 1, figsize=(16, 5), sharex=True,
                                           gridspec_kw={'height_ratios':[3,1]})
    fig.suptitle('阶段一：机械臂重启及加电保温 任务规划结果', fontsize=14, fontweight='bold')

    color = phase_colors[1]
    tasks = sub_tasks[1]

    # Arm timeline: two rows
    labels = ['大臂重启加电保温\n(运动前12h)', '小臂重启加电保温\n(运动前5h)']
    for ti, (name, ts, te) in enumerate(tasks):
        y = 2 - ti
        dur = te - ts
        ax_arm.barh(y, dur, left=ts, height=0.55, color=color,
                    alpha=0.7, edgecolor='#546E7A', lw=1.2)
        ax_arm.text(ts + dur/2, y, f'{name}\n[{ts}s, {te}s]  ({dur}s)',
                    ha='center', va='center', fontsize=8, color='white', fontweight='bold')

    # Waiting period annotation
    ax_arm.annotate('', xy=(25350, 1.3), xytext=(980, 1.7),
                    arrowprops=dict(arrowstyle='->', color='gray', lw=1.5, ls='--'))
    ax_arm.text(13000, 1.8, '等待期 (约6.7小时)', ha='center', fontsize=9, color='gray',
                fontstyle='italic')

    # WaitForMotion bar
    ax_arm.barh(0.5, 27600-25350, left=25350, height=0.4, color='#E0E0E0',
                edgecolor='gray', lw=0.8, alpha=0.6)
    ax_arm.text(26475, 0.5, '等待运动开始\n[25350, 27600]', ha='center', va='center',
                fontsize=7, color='#666')

    ax_arm.set_yticks([2, 1, 0.5])
    ax_arm.set_yticklabels(['1a: 大臂重启', '1b: 小臂重启', '等待'], fontsize=9)
    ax_arm.set_ylim(0, 2.8)
    ax_arm.set_ylabel('子任务', fontsize=11)
    ax_arm.grid(axis='x', alpha=0.3, ls='--')

    # Time markers
    for t, label, clr in [(0,'T=0\n任务起始','#333'), (980,'T=980\n大臂完成','#546E7A'),
                           (25200,'T=25200\n小臂开始','#546E7A'), (27600,'T=27600\nPhase2开始','#42A5F5')]:
        ax_arm.axvline(t, color=clr, ls=':', lw=1, alpha=0.6)
        ax_arm.text(t, 2.6, label, ha='center', va='bottom', fontsize=6.5, color=clr)

    # Comm windows
    for ts, te, on in comm_windows:
        if te <= 0 or ts >= 28000: continue
        ts2 = max(ts, 0); te2 = min(te, 28000)
        c = '#4CAF50' if on else '#EF9A9A'; a = 0.6 if on else 0.3
        ax_comm.barh(0.5, te2-ts2, left=ts2, height=0.6, color=c, ec='gray', lw=0.5, alpha=a)
        if on and te2-ts2 > 1000:
            ax_comm.text((ts2+te2)/2, 0.5, f'通信可用\n[{ts},{te}]',
                         ha='center', va='center', fontsize=6.5, color='white', fontweight='bold')
    ax_comm.set_ylabel('通信窗口', fontsize=10)
    ax_comm.set_xlabel('时间 (s)', fontsize=11)
    ax_comm.set_yticks([]); ax_comm.set_ylim(0,1)
    ax_comm.grid(axis='x', alpha=0.3, ls='--')
    ax_comm.set_xlim(-500, 28500)

    plt.tight_layout()
    plt.savefig('/opt/cursor/artifacts/gantt_phase1.png', dpi=200, bbox_inches='tight')
    plt.savefig('/workspace/examples/ArmMission/gantt_phase1.png', dpi=200, bbox_inches='tight')
    print("Saved: gantt_phase1.png")
    plt.close()

# ════════════════════════════════════════
# CHART B: Phase 2-6 overall + zoom
# ════════════════════════════════════════
def plot_phase2to6():
    fig = plt.figure(figsize=(18, 18))
    gs = GridSpec(5, 5, figure=fig, height_ratios=[3.5, 0.8, 0.8, 0.2, 5],
                  hspace=0.35, wspace=0.3)

    fig.suptitle('阶段二至阶段六：机械臂作业任务规划结果 (含各阶段局部放大)',
                 fontsize=14, fontweight='bold', y=0.995)

    # ── Top: overall ──
    ax_m = fig.add_subplot(gs[0, :])
    ax_c = fig.add_subplot(gs[1, :], sharex=ax_m)
    ax_o = fig.add_subplot(gs[2, :], sharex=ax_m)

    y_map = {2:5, 3:4, 4:3, 5:2, 6:1}
    for pid in [2,3,4,5,6]:
        tasks = sub_tasks[pid]
        color = phase_colors[pid]
        y = y_map[pid]
        pr = phase_ranges[pid]

        # Phase background
        ax_m.barh(y, pr[1]-pr[0], left=pr[0], height=0.7, color=color, alpha=0.2,
                  edgecolor=color, lw=1.5)

        # Sub-tasks
        for ti, (name, ts, te) in enumerate(tasks):
            shade = 0.5 + 0.4*(ti%2)
            ax_m.barh(y, te-ts, left=ts, height=0.5, color=color, alpha=shade,
                     edgecolor='white', lw=0.5)

        # Label
        ax_m.text(pr[0]-80, y, phase_names[pid], ha='right', va='center',
                  fontsize=8, fontweight='bold', color=color)

        # SWA marker
        if pid in [4,5]:
            ax_m.text(pr[1]+50, y, '⚠SWA', fontsize=7, color='red', fontweight='bold', va='center')

    ax_m.set_yticks(list(y_map.values()))
    ax_m.set_yticklabels([phase_names[k] for k in y_map], fontsize=8)
    ax_m.set_ylim(0.2, 6); ax_m.grid(axis='x', alpha=0.3, ls='--')
    ax_m.set_ylabel('任务阶段', fontsize=11)
    ax_m.legend(handles=[mpatches.Patch(fc=phase_colors[k], alpha=0.7, label=phase_names[k]) for k in [2,3,4,5,6]],
                loc='upper right', fontsize=7, ncol=3, framealpha=0.9)

    # Zoom region boxes with colors matching phases
    zoom_configs = [
        ((27400,31200), '#42A5F5', '--'),   # Phase 2
        ((31050,33050), '#66BB6A', '--'),   # Phase 3
        ((32900,33800), '#FF7043', '--'),   # Phase 4
        ((33680,34260), '#AB47BC', '--'),   # Phase 5
        ((34140,35820), '#FFA726', '--'),   # Phase 6
    ]
    for (xmin,xmax), clr, ls in zoom_configs:
        rect = mpatches.FancyBboxPatch((xmin, 0.3), xmax-xmin, 5.5,
                boxstyle="round,pad=0", fc='none', ec=clr, lw=2, ls=ls, alpha=0.7)
        ax_m.add_patch(rect)

    # Comm
    for ts, te, on in comm_windows:
        if te < 27000 or ts > 36500: continue
        c2 = '#4CAF50' if on else '#EF9A9A'; a2 = 0.6 if on else 0.3
        ax_c.barh(0.5, te-ts, left=ts, height=0.6, color=c2, ec='gray', lw=0.5, alpha=a2)
        if on and te-ts > 1000:
            ax_c.text((max(ts,27000)+min(te,36500))/2, 0.5, f'通信可用 [{ts},{te}]',
                     ha='center', va='center', fontsize=6.5, color='white', fontweight='bold')
    ax_c.set_ylabel('通信', fontsize=9); ax_c.set_yticks([]); ax_c.set_ylim(0,1)
    ax_c.grid(axis='x', alpha=0.3, ls='--')

    # Occ
    for ts, te, act in occ_windows:
        if te < 27000 or ts > 36500: continue
        c3 = '#F44336' if act else '#C8E6C9'; a3 = 0.7 if act else 0.15
        ax_o.barh(0.5, te-ts, left=ts, height=0.6, color=c3, ec='gray', lw=0.5, alpha=a3)
    ax_o.text(33000, 0.5, 'SWA遮挡不活跃 (整个Phase2-6期间)', ha='center', va='center',
              fontsize=7, color='#666', fontstyle='italic')
    ax_o.set_ylabel('遮挡', fontsize=9); ax_o.set_xlabel('时间 (s)', fontsize=10)
    ax_o.set_yticks([]); ax_o.set_ylim(0,1)
    ax_o.grid(axis='x', alpha=0.3, ls='--')
    ax_o.set_xlim(27000, 36500)

    # ── Bottom: 5 zoom panels ──
    zoom_phase_map = [
        (2, (27400, 31200), "Phase 2 局部放大：平台状态设置 (3530s)"),
        (3, (31050, 33050), "Phase 3 局部放大：大臂运动至组合 (1840s)"),
        (4, (32900, 33800), "Phase 4 局部放大：小臂至SWA (770s) ⚠"),
        (5, (33680, 34260), "Phase 5 局部放大：视觉捕获SWA (460s) ⚠"),
        (6, (34140, 35820), "Phase 6 局部放大：小臂独立设置 (1560s)"),
    ]

    for zi, (pid, (xmin, xmax), ztitle) in enumerate(zoom_phase_map):
        ax_z = fig.add_subplot(gs[4, zi])
        tasks = sub_tasks[pid]
        color = phase_colors[pid]
        n = len(tasks)

        for ti, (name, ts, te) in enumerate(tasks):
            y_r = n - ti
            shade = 0.5 + 0.4*(ti%2)
            ax_z.barh(y_r, te-ts, left=ts, height=0.7, color=color, alpha=shade,
                     edgecolor='white', lw=0.8)
            dur = te - ts
            bar_frac = dur / (xmax - xmin)
            if bar_frac > 0.12:
                ax_z.text((ts+te)/2, y_r, f'{name}\n({dur}s)',
                         ha='center', va='center', fontsize=6, color='white', fontweight='bold')
            elif bar_frac > 0.04:
                ax_z.text((ts+te)/2, y_r, f'{name}', ha='center', va='center',
                         fontsize=5.5, color='white', fontweight='bold')
                ax_z.text((ts+te)/2, y_r-0.3, f'({dur}s)', ha='center', va='top',
                         fontsize=5, color='#555')
            else:
                ax_z.text(te+8, y_r, f'{name} ({dur}s)', ha='left', va='center',
                         fontsize=5.5, color='#333')

        ax_z.set_xlim(xmin, xmax)
        ax_z.set_ylim(0.2, n+0.8)
        ax_z.set_yticks(range(1, n+1))
        ax_z.set_yticklabels([t[0] for t in reversed(tasks)], fontsize=6)
        ax_z.grid(axis='x', alpha=0.3, ls='--')
        ax_z.set_xlabel('时间 (s)', fontsize=7)
        ax_z.set_title(ztitle, fontsize=8, fontweight='bold', color=color)
        for sp in ax_z.spines.values():
            sp.set_edgecolor(color); sp.set_linewidth(2)

    plt.savefig('/opt/cursor/artifacts/gantt_phase2to6_zoom.png', dpi=200, bbox_inches='tight')
    plt.savefig('/workspace/examples/ArmMission/gantt_phase2to6_zoom.png', dpi=200, bbox_inches='tight')
    print("Saved: gantt_phase2to6_zoom.png")
    plt.close()


if __name__ == '__main__':
    plot_phase1()
    plot_phase2to6()
    print("Done.")
