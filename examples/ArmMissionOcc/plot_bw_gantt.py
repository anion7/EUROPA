#!/usr/bin/env python3
"""
Black-and-white Gantt charts for the occlusion-conflict ArmMission scenario.
Designed for monochrome printing: uses hatching, line styles, and gray levels.
Three figures:
  1. Communication windows & SWA occlusion timeline
  2. Per-phase sub-task Gantt (Phase 1 separate, Phase 2-6 with zooms)
  3. Overall mission Gantt with zoom insets
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
# DATA  (occlusion-conflict scenario)
# ════════════════════════════════════════
comm = [
    (0,2060,True),(2060,4590,False),(4590,8020,True),(8020,10550,False),
    (10550,14090,True),(14090,16610,False),(16610,20120,True),(20120,22640,False),
    (22640,26030,True),(26030,28570,False),(28570,31880,True),(31880,34420,False),
    (34420,37710,True),(37710,40240,False),
    (40240,43570,True),(43570,46100,False),
    (46100,49520,True),(49520,52040,False),(52040,55000,True),
]
occ = [
    (0,36770,False),(36770,37200,True),(37200,50470,False),
    (50470,51120,True),(51120,55000,False),
]

# EUROPA plan result (TLE-computed, exact times from solver)
plan = [
    ('BigArmRestart',   0,      980,   '1a'),
    ('SmallArmRestart', 2060,   2210,  '1b'),
    ('Phase2Settings',  4590,   8120,  '2'),
    ('WaitForMotion',   8120,   34420, 'W'),
    ('Phase3',          34420,  36260, '3'),
    ('IdleOcc',         36260,  40240, 'W'),
    ('Phase4',          40240,  41010, '4'),
    ('Phase5',          41010,  41470, '5'),
    ('Phase6',          41470,  43030, '6'),
]

sub_tasks = {
    '1a': [("大臂重启加电保温", 0, 980)],
    '1b': [("小臂重启加电保温", 2060, 2210)],
    '2': [("太阳帆板设置",4590,7000),("舱外相机设置",7000,7960),
          ("禁止自主能源",7960,8000),("禁止电源保护",8000,8060),
          ("禁止母线掉电",8060,8100),("禁止热控辐射",8100,8120)],
    '3': [("小臂任务前重启",34420,34960),("大臂运动准备",34960,35160),
          ("转移至中间构型",35160,35520),("大臂至舱I上方",35520,35960),
          ("大臂至组合构型",35960,36260)],
    '4': [("小臂至SWA 500mm",40240,40610),("小臂至SWA 300mm",40610,41010)],
    '5': [("视觉精定位109mm",41010,41170),("小臂捕获SWA",41170,41470)],
    '6': [("大臂给小臂断电",41470,41730),("小臂SWA上电",41730,42130),
          ("释放转接件(a)",42130,42345),("视觉伺服105mm",42345,42485),
          ("释放转接件(b)",42485,42730),("小臂手爪收拢",42730,43030)],
}

phase_labels = {
    '1a':'Phase1a:大臂重启','1b':'Phase1b:小臂重启',
    '2':'Phase2:平台设置','3':'Phase3:大臂至组合',
    '4':'Phase4:小臂至SWA','5':'Phase5:视觉捕获','6':'Phase6:独立设置'
}

# B&W styling: gray levels + hatching
phase_gray   = {'1a':0.70,'1b':0.70,'2':0.50,'3':0.35,'4':0.20,'5':0.55,'6':0.42,'W':0.92}
phase_hatch  = {'1a':'//','1b':'//','2':'','3':'\\\\','4':'xx','5':'..','6':'--','W':''}

def gray(level): return (level, level, level)

# ════════════════════════════════════════
# FIGURE 1: Comm & Occlusion Timeline
# ════════════════════════════════════════
def fig1_comm_occ():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 4), sharex=True,
                                     gridspec_kw={'height_ratios':[1,1]})
    fig.suptitle('图X-1 通信窗口与SWA遮挡状态时间线', fontsize=13, fontweight='bold')

    for ts, te, on in comm:
        fc = gray(0.85) if on else gray(0.97)
        hatch = '' if on else '///'
        ec = 'black'
        ax1.barh(0.5, te-ts, left=ts, height=0.6, facecolor=fc, edgecolor=ec,
                 lw=0.8, hatch=hatch)
        label = "通信可用" if on else "通信中断"
        if te-ts > 2000:
            ax1.text((ts+te)/2, 0.5, f'{label}\n[{ts},{te}]',
                     ha='center', va='center', fontsize=6.5, color='black')
    ax1.set_ylabel('通信窗口', fontsize=10)
    ax1.set_yticks([0.5]); ax1.set_yticklabels(['CommWindow'], fontsize=9)
    ax1.set_ylim(0,1); ax1.grid(axis='x', alpha=0.3, ls='--')
    ax1.legend(handles=[
        mpatches.Patch(fc=gray(0.85), ec='black', label='通信可用 (InComms)'),
        mpatches.Patch(fc=gray(0.97), ec='black', hatch='///', label='通信中断 (OutComms)'),
    ], loc='upper right', fontsize=7.5)

    for ts, te, act in occ:
        fc = gray(0.30) if act else gray(0.95)
        hatch = 'xxx' if act else ''
        ax2.barh(0.5, te-ts, left=ts, height=0.6, facecolor=fc, edgecolor='black',
                 lw=0.8, hatch=hatch)
        if act:
            ax2.text((ts+te)/2, 0.5, f'遮挡\n[{ts},{te}]',
                     ha='center', va='center', fontsize=6.5, color='white', fontweight='bold')
    ax2.set_ylabel('SWA遮挡', fontsize=10)
    ax2.set_xlabel('时间 (s)', fontsize=10)
    ax2.set_yticks([0.5]); ax2.set_yticklabels(['OcclusionSWA'], fontsize=9)
    ax2.set_ylim(0,1); ax2.grid(axis='x', alpha=0.3, ls='--')
    ax2.legend(handles=[
        mpatches.Patch(fc=gray(0.30), ec='black', hatch='xxx', label='遮挡活跃 (Active)'),
        mpatches.Patch(fc=gray(0.95), ec='black', label='遮挡不活跃 (Inactive)'),
    ], loc='upper right', fontsize=7.5)
    ax2.set_xlim(-500, 56000)

    plt.tight_layout()
    plt.savefig('/opt/cursor/artifacts/bw_gantt_1_comm_occ.png', dpi=200, bbox_inches='tight')
    plt.savefig('/workspace/examples/ArmMissionOcc/bw_gantt_1_comm_occ.png', dpi=200, bbox_inches='tight')
    print("Saved: bw_gantt_1_comm_occ.png")
    plt.close()

# ════════════════════════════════════════
# FIGURE 2: Per-phase sub-task panels
# ════════════════════════════════════════
def fig2_per_phase():
    phase_ids = ['1a','1b','2','3','4','5','6']
    fig, axes = plt.subplots(len(phase_ids), 1, figsize=(16, 16), sharex=False)
    fig.suptitle('图X-2 各阶段子任务规划结果', fontsize=13, fontweight='bold', y=0.998)

    for idx, pid in enumerate(phase_ids):
        ax = axes[idx]
        tasks = sub_tasks[pid]
        g = phase_gray[pid]
        h = phase_hatch[pid]
        n = len(tasks)

        for ti, (name, ts, te) in enumerate(tasks):
            y = n - ti
            shade = g - 0.08*(ti%2)
            ax.barh(y, te-ts, left=ts, height=0.65, facecolor=gray(shade),
                    edgecolor='black', lw=0.8, hatch=h)
            dur = te-ts
            txt_color = 'white' if shade < 0.5 else 'black'
            if dur > 80:
                ax.text(ts+dur/2, y, f'{name} ({dur}s)',
                        ha='center', va='center', fontsize=6.5, color=txt_color, fontweight='bold')
            else:
                ax.text(te+20, y, f'{name} ({dur}s)',
                        ha='left', va='center', fontsize=6.5, color='black')

        ax.set_yticks(range(1, n+1))
        ax.set_yticklabels([t[0] for t in reversed(tasks)], fontsize=7)
        ax.set_ylim(0.3, n+0.7)
        all_ts = [t[1] for t in tasks]; all_te = [t[2] for t in tasks]
        margin = max(80, (max(all_te)-min(all_ts))*0.08)
        ax.set_xlim(min(all_ts)-margin, max(all_te)+margin)
        ax.grid(axis='x', alpha=0.3, ls='--')
        ax.set_xlabel('时间 (s)', fontsize=8)

        title = phase_labels.get(pid, pid)
        swa_mark = ' ⚠遮挡约束' if pid in ['4','5'] else ''
        ax.set_title(f'{title}  [{min(all_ts)}s ~ {max(all_te)}s]{swa_mark}',
                     fontsize=9, fontweight='bold', loc='left')

    plt.tight_layout()
    plt.savefig('/opt/cursor/artifacts/bw_gantt_2_per_phase.png', dpi=200, bbox_inches='tight')
    plt.savefig('/workspace/examples/ArmMissionOcc/bw_gantt_2_per_phase.png', dpi=200, bbox_inches='tight')
    print("Saved: bw_gantt_2_per_phase.png")
    plt.close()

# ════════════════════════════════════════
# FIGURE 3: Overall + zoom insets
# ════════════════════════════════════════
def fig3_overall():
    fig = plt.figure(figsize=(18, 17))
    gs = GridSpec(4, 5, figure=fig, height_ratios=[4, 0.9, 0.9, 5.5],
                  hspace=0.4, wspace=0.3)
    fig.suptitle('图X-3 机械臂全任务规划结果甘特图（含各阶段局部放大）',
                 fontsize=13, fontweight='bold', y=0.995)

    ax_m = fig.add_subplot(gs[0, :])
    ax_c = fig.add_subplot(gs[1, :], sharex=ax_m)
    ax_o = fig.add_subplot(gs[2, :], sharex=ax_m)

    # ── Main Arm timeline ──
    y_map = {'1a':8,'1b':7,'W1':6,'2':5,'3':4,'4':3,'5':2,'6':1}
    for name, ts, te, pid in plan:
        if pid == 'W':
            y_key = 'W1'
            ax_m.barh(y_map.get(y_key,6), te-ts, left=ts, height=0.5,
                      facecolor=gray(0.92), edgecolor='gray', lw=0.6, ls='--')
            if te-ts > 800:
                ax_m.text((ts+te)/2, y_map.get(y_key,6), f'等待[{ts},{te}]',
                         ha='center', va='center', fontsize=5.5, color='gray')
            continue
        y = y_map.get(pid, 6)
        g = phase_gray[pid]; h = phase_hatch[pid]
        ax_m.barh(y, te-ts, left=ts, height=0.6, facecolor=gray(g),
                  edgecolor='black', lw=1, hatch=h)
        label_text = phase_labels.get(pid, name)
        if te-ts > 1000:
            txt_c = 'white' if g < 0.5 else 'black'
            ax_m.text((ts+te)/2, y, f'{label_text}\n[{ts},{te}]',
                     ha='center', va='center', fontsize=6, color=txt_c, fontweight='bold')

    # Occlusion markers on Phase4/5 region
    for ots, ote, act in occ:
        if act and ots < 36000:
            ax_m.axvspan(ots, ote, ymin=0, ymax=1, color='black', alpha=0.08)
            ax_m.text((ots+ote)/2, 8.5, f'遮挡\n[{ots},{ote}]', ha='center', va='bottom',
                     fontsize=5.5, color='black', fontstyle='italic')

    y_labels = ['Phase6','Phase5','Phase4','Phase3','Phase2','等待','Phase1b','Phase1a']
    ax_m.set_yticks(range(1, 9))
    ax_m.set_yticklabels(y_labels, fontsize=7.5)
    ax_m.set_ylim(0, 9.5); ax_m.grid(axis='x', alpha=0.3, ls='--')
    ax_m.set_ylabel('任务阶段', fontsize=10)

    legend_items = []
    for pid in ['1a','2','3','4','5','6']:
        legend_items.append(mpatches.Patch(fc=gray(phase_gray[pid]), ec='black',
                            hatch=phase_hatch[pid], label=phase_labels.get(pid,pid)))
    legend_items.append(mpatches.Patch(fc=gray(0.92), ec='gray', ls='--', label='等待/空闲'))
    ax_m.legend(handles=legend_items, loc='upper left', fontsize=6.5, ncol=4, framealpha=0.9)

    # Zoom boxes
    zoom_specs = [
        ((4400,8300),'Phase2'), ((34300,36400),'Phase3'),
        ((40100,41100),'Phase4'), ((40950,41550),'Phase5'),
        ((41400,43150),'Phase6'),
    ]
    for (xmin,xmax), _ in zoom_specs:
        ax_m.add_patch(mpatches.FancyBboxPatch((xmin,0.1), xmax-xmin, 9,
            boxstyle="round,pad=0", fc='none', ec='black', lw=1.5, ls='--', alpha=0.5))

    # ── Comm ──
    for ts, te, on in comm:
        fc = gray(0.85) if on else gray(0.97)
        hatch = '' if on else '///'
        ax_c.barh(0.5, te-ts, left=ts, height=0.6, fc=fc, ec='black', lw=0.5, hatch=hatch)
        if on and te-ts > 2500:
            ax_c.text((ts+te)/2, 0.5, f'[{ts},{te}]', ha='center', va='center', fontsize=5.5)
    ax_c.set_ylabel('通信', fontsize=8); ax_c.set_yticks([]); ax_c.set_ylim(0,1)
    ax_c.grid(axis='x', alpha=0.3, ls='--')

    # ── Occ ──
    for ts, te, act in occ:
        fc = gray(0.30) if act else gray(0.95)
        hatch = 'xxx' if act else ''
        ax_o.barh(0.5, te-ts, left=ts, height=0.6, fc=fc, ec='black', lw=0.5, hatch=hatch)
        if act:
            ax_o.text((ts+te)/2, 0.5, f'[{ts},{te}]', ha='center', va='center',
                     fontsize=5.5, color='white', fontweight='bold')
    ax_o.set_ylabel('遮挡', fontsize=8); ax_o.set_xlabel('时间 (s)', fontsize=9)
    ax_o.set_yticks([]); ax_o.set_ylim(0,1)
    ax_o.grid(axis='x', alpha=0.3, ls='--')
    ax_o.set_xlim(-500, 48000)

    # ── Zoom panels ──
    zoom_phase_map = [
        ('2', (4400,8300), "Phase2局部放大: 平台设置"),
        ('3', (34300,36400), "Phase3局部放大: 大臂至组合"),
        ('4', (40100,41100), "Phase4局部放大: 小臂至SWA ⚠"),
        ('5', (40950,41550), "Phase5局部放大: 视觉捕获 ⚠"),
        ('6', (41400,43150), "Phase6局部放大: 独立设置"),
    ]

    for zi, (pid, (xmin, xmax), ztitle) in enumerate(zoom_phase_map):
        ax_z = fig.add_subplot(gs[3, zi])
        tasks = sub_tasks[pid]
        g = phase_gray[pid]; h = phase_hatch[pid]
        n = len(tasks)

        # Draw occlusion bands for Phase 4/5
        if pid in ['4','5']:
            for ots, ote, act in occ:
                if act and ote > xmin and ots < xmax:
                    ax_z.axvspan(max(ots,xmin), min(ote,xmax), color='black', alpha=0.12)
                    ax_z.text((max(ots,xmin)+min(ote,xmax))/2, n+0.3,
                             f'遮挡[{ots},{ote}]', ha='center', va='bottom',
                             fontsize=5, fontstyle='italic')

        for ti, (name, ts, te) in enumerate(tasks):
            y_r = n - ti
            shade = g - 0.08*(ti%2)
            ax_z.barh(y_r, te-ts, left=ts, height=0.7, facecolor=gray(shade),
                     edgecolor='black', lw=0.8, hatch=h)
            dur = te-ts
            bar_frac = dur / (xmax-xmin)
            txt_c = 'white' if shade < 0.5 else 'black'
            if bar_frac > 0.1:
                ax_z.text((ts+te)/2, y_r, f'{name}\n({dur}s)',
                         ha='center', va='center', fontsize=5.5, color=txt_c, fontweight='bold')
            elif bar_frac > 0.03:
                ax_z.text((ts+te)/2, y_r, name, ha='center', va='center',
                         fontsize=5, color=txt_c, fontweight='bold')
            else:
                ax_z.text(te+8, y_r, f'{name} ({dur}s)', ha='left', va='center',
                         fontsize=5.5, color='black')

        ax_z.set_xlim(xmin, xmax)
        ax_z.set_ylim(0.2, n+0.8)
        ax_z.set_yticks(range(1, n+1))
        ax_z.set_yticklabels([t[0] for t in reversed(tasks)], fontsize=5.5)
        ax_z.grid(axis='x', alpha=0.3, ls='--')
        ax_z.set_xlabel('时间 (s)', fontsize=7)
        ax_z.set_title(ztitle, fontsize=7.5, fontweight='bold')
        for sp in ax_z.spines.values():
            sp.set_edgecolor('black'); sp.set_linewidth(1.5); sp.set_linestyle('--')

    plt.savefig('/opt/cursor/artifacts/bw_gantt_3_overall_zoom.png', dpi=200, bbox_inches='tight')
    plt.savefig('/workspace/examples/ArmMissionOcc/bw_gantt_3_overall_zoom.png', dpi=200, bbox_inches='tight')
    print("Saved: bw_gantt_3_overall_zoom.png")
    plt.close()


if __name__ == '__main__':
    fig1_comm_occ()
    fig2_per_phase()
    fig3_overall()
    print("All B&W charts generated.")
