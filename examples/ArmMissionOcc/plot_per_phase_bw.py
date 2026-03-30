#!/usr/bin/env python3
"""
Generate bw_gantt_2_per_phase for both Case 1 and Case 2.
Each figure has 7 panels (Phase1a, 1b, 2, 3, 4, 5, 6) showing sub-task details.
B&W: gray levels + hatching patterns for monochrome printing.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

try: plt.rcParams['font.family'] = ['Noto Sans CJK JP', 'sans-serif']
except: pass
plt.rcParams['axes.unicode_minus'] = False

def gray(l): return (l, l, l)

# Phase styling
PG = {'1a':.70, '1b':.70, '2':.50, '3':.35, '4':.20, '5':.55, '6':.42}
PH = {'1a':'//', '1b':'//', '2':'', '3':'\\\\', '4':'xx', '5':'..', '6':'--'}
PL = {
    '1a':'Phase1a:大臂重启加电保温', '1b':'Phase1b:小臂重启加电保温',
    '2':'Phase2:平台状态设置', '3':'Phase3:大臂运动至组合构型',
    '4':'Phase4:小臂运动至SWA', '5':'Phase5:视觉捕获SWA', '6':'Phase6:小臂独立工作设置'
}

def make_subs(case_data):
    """Build sub-task lists from case timing data."""
    d = case_data; s = {}
    s['1a'] = [("大臂重启加电保温", d['bigarm'][0], d['bigarm'][1])]
    s['1b'] = [("小臂重启加电保温", d['smallarm'][0], d['smallarm'][1])]
    t = d['phase2'][0]
    s['2'] = [("太阳帆板设置",t,t+2410), ("舱外相机设置",t+2410,t+3370),
              ("禁止自主能源",t+3370,t+3410), ("禁止电源保护",t+3410,t+3470),
              ("禁止母线掉电",t+3470,t+3510), ("禁止热控辐射",t+3510,t+3530)]
    t = d['phase3'][0]
    s['3'] = [("小臂任务前重启",t,t+540), ("大臂运动准备",t+540,t+740),
              ("转移至中间构型",t+740,t+1100), ("大臂至舱I上方",t+1100,t+1540),
              ("大臂至组合构型",t+1540,t+1840)]
    t = d['phase4'][0]
    s['4'] = [("小臂至SWA 500mm",t,t+370), ("小臂至SWA 300mm",t+370,t+770)]
    t = d['phase5'][0]
    s['5'] = [("视觉精定位109mm",t,t+160), ("小臂捕获SWA",t+160,t+460)]
    t = d['phase6'][0]
    s['6'] = [("大臂给小臂断电",t,t+260), ("小臂SWA上电",t+260,t+660),
              ("释放转接件(a)",t+660,t+875), ("视觉伺服105mm",t+875,t+1015),
              ("释放转接件(b)",t+1015,t+1260), ("小臂手爪收拢",t+1260,t+1560)]
    return s

CASES = {
    1: {
        'name': '算例一（无遮挡冲突）',
        'bigarm': (9380, 10360), 'smallarm': (37250, 37400),
        'phase2': (6130, 9660), 'phase3': (53560, 55400),
        'phase4': (55400, 56170), 'phase5': (56170, 56630),
        'phase6': (59430, 60990),
    },
    2: {
        'name': '算例二（遮挡冲突）',
        'bigarm': (15250, 16230), 'smallarm': (47640, 47790),
        'phase2': (6130, 9660), 'phase3': (59430, 61270),
        'phase4': (65360, 66130), 'phase5': (66130, 66590),
        'phase6': (66590, 68150),
    },
}

# SWA occlusion events (for marking on Phase4/5 panels)
OCC_ACTIVE = [(61750, 62180), (75450, 76110)]


def plot_per_phase(case_id):
    d = CASES[case_id]
    subs = make_subs(d)
    phase_ids = ['1a', '1b', '2', '3', '4', '5', '6']

    fig, axes = plt.subplots(len(phase_ids), 1, figsize=(16, 18), sharex=False)
    fig.suptitle(f'各阶段子任务规划结果 ({d["name"]})',
                 fontsize=14, fontweight='bold', y=0.998)

    for idx, pid in enumerate(phase_ids):
        ax = axes[idx]
        tasks = subs[pid]
        g = PG[pid]
        h = PH[pid]
        n = len(tasks)

        # Compute x-range
        all_ts = [t[1] for t in tasks]
        all_te = [t[2] for t in tasks]
        span = max(all_te) - min(all_ts)
        margin = max(100, span * 0.08)
        xmin = min(all_ts) - margin
        xmax = max(all_te) + margin

        # Draw occlusion bands for Phase4/5
        if pid in ['4', '5']:
            for ots, ote in OCC_ACTIVE:
                if ote > xmin and ots < xmax:
                    ax.axvspan(max(ots, xmin), min(ote, xmax),
                               color='black', alpha=0.12, zorder=0)
                    ax.text((max(ots, xmin) + min(ote, xmax)) / 2, n + 0.4,
                            f'遮挡区间[{ots},{ote}]', ha='center', va='bottom',
                            fontsize=6, fontstyle='italic', color='#555')

        # Draw sub-task bars
        for ti, (name, ts, te) in enumerate(tasks):
            y = n - ti
            shade = g - 0.08 * (ti % 2)
            ax.barh(y, te - ts, left=ts, height=0.65,
                    facecolor=gray(shade), edgecolor='black', lw=0.8, hatch=h)
            dur = te - ts
            txt_color = 'white' if shade < 0.5 else 'black'
            bar_frac = dur / (xmax - xmin) if xmax > xmin else 1

            if bar_frac > 0.12:
                ax.text(ts + dur / 2, y, f'{name} ({dur}s)',
                        ha='center', va='center', fontsize=7,
                        color=txt_color, fontweight='bold')
            elif bar_frac > 0.04:
                ax.text(ts + dur / 2, y, f'{name}',
                        ha='center', va='center', fontsize=6.5,
                        color=txt_color, fontweight='bold')
                ax.text(ts + dur / 2, y - 0.32, f'({dur}s)',
                        ha='center', va='top', fontsize=5.5, color='#444')
            else:
                ax.text(te + 15, y, f'{name} ({dur}s)',
                        ha='left', va='center', fontsize=6.5, color='black')

        # Y-axis: sub-task names
        ax.set_yticks(range(1, n + 1))
        ax.set_yticklabels([t[0] for t in reversed(tasks)], fontsize=7)
        ax.set_ylim(0.3, n + 0.7)
        ax.set_xlim(xmin, xmax)
        ax.grid(axis='x', alpha=0.3, ls='--')
        ax.set_xlabel('时间 (s)', fontsize=8)

        # Title with time range and SWA marker
        swa_mark = '  ⚠遮挡约束' if pid in ['4', '5'] else ''
        phase_start = min(all_ts)
        phase_end = max(all_te)
        ax.set_title(
            f'{PL[pid]}  [{phase_start}s ~ {phase_end}s]  '
            f'(总时长 {phase_end - phase_start}s){swa_mark}',
            fontsize=9.5, fontweight='bold', loc='left')

    plt.tight_layout()

    for path in [
        f'/opt/cursor/artifacts/bw_case{case_id}_per_phase.png',
        f'/workspace/examples/ArmMissionOcc/bw_case{case_id}_per_phase.png',
    ]:
        plt.savefig(path, dpi=200, bbox_inches='tight')

    plt.close()
    print(f'Saved: bw_case{case_id}_per_phase.png')


if __name__ == '__main__':
    plot_per_phase(1)
    plot_per_phase(2)
    print('Done.')
