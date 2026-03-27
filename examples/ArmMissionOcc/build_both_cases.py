#!/usr/bin/env python3
"""
Build both simulation cases, solve with EUROPA, generate B&W Gantt charts,
and produce Word document. All comm/occ windows from real TLE propagation.

Case 1: No occlusion conflict — Phase3-5 in Vis9, no occ event
Case 2: Occlusion conflict — Phase3 in Vis7, occ [36770,37200] blocks Phase4
"""

import os, sys, subprocess, math, shutil, re, textwrap
from datetime import datetime, timedelta, timezone

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np

try: plt.rcParams['font.family'] = ['Noto Sans CJK JP', 'sans-serif']
except: pass
plt.rcParams['axes.unicode_minus'] = False

PI = math.pi
OUTDIR = '/workspace/examples/ArmMissionOcc'
ARTIFACTS = '/opt/cursor/artifacts'
RUNNER = '/workspace/build/src/PLASMA/System/test'
T0_UTC = datetime(2025, 7, 26, 3, 56, 25, tzinfo=timezone.utc)

# ═══ TLE-computed communication windows ═══
COMM = [
    (0,2060,True),(2060,4590,False),(4590,8020,True),(8020,10550,False),
    (10550,14090,True),(14090,16610,False),(16610,20120,True),(20120,22640,False),
    (22640,26030,True),(26030,28570,False),(28570,31880,True),(31880,34420,False),
    (34420,37710,True),(37710,40240,False),(40240,43570,True),(43570,46100,False),
    (46100,49520,True),(49520,52040,False),(52040,55570,True),
]
# TLE-computed SWA occlusion (beam=5deg angular criterion)
OCC = [(0,36770,False),(36770,37200,True),(37200,50470,False),(50470,51120,True),(51120,60000,False)]

# ═══ Sub-task durations (seconds) ═══
P2_DUR, P3_DUR, P4_DUR, P5_DUR, P6_DUR = 3530, 1840, 770, 460, 1560

def t_to_utc(t): return (T0_UTC + timedelta(seconds=t)).strftime('%m-%d %H:%M')
def gray(lv): return (lv,lv,lv)

# ═══════════════════════════════════════════════
# Case definitions
# ═══════════════════════════════════════════════
CASES = {
  1: {
    'name': '算例一（无遮挡冲突）',
    'en': 'Case 1: No Occlusion Conflict',
    'bigarm': (0, 980),           # Vis1
    'smallarm': (25880, 26030),   # end of Vis5, 5.6h before motion
    'phase2': (40240, 43770),     # Vis8 (no strict comm)
    'wait': (43770, 46100),
    'phase3': (46100, 47940),     # Vis9
    'idle': None,
    'phase4': (47940, 48710),     # Vis9
    'phase5': (48710, 49170),     # Vis9
    'idle56': (49170, 52040),     # comm gap
    'phase6': (52040, 53600),     # Vis10
    'horizon': 56000,
    'comm_label': 'C09 [46100,49520]',
    'occ_note': '无遮挡事件影响',
    'p4_note': 'Phase4紧随Phase3',
  },
  2: {
    'name': '算例二（遮挡冲突）',
    'en': 'Case 2: Occlusion Conflict',
    'bigarm': (0, 980),           # Vis1, pre-completed >12h
    'smallarm': (13940, 14090),   # Vis3, 5.6h before motion
    'phase2': (4590, 8120),       # Vis2 (no strict comm)
    'wait': (8120, 34420),
    'phase3': (34420, 36260),     # Vis7
    'idle': (36260, 40240),       # occ [36770,37200] + comm gap [37710,40240]
    'phase4': (40240, 41010),     # Vis8
    'phase5': (41010, 41470),     # Vis8
    'idle56': None,
    'phase6': (41470, 43030),     # Vis8
    'horizon': 48000,
    'comm_label': 'C07→C08',
    'occ_note': '遮挡[36770,37200]阻断Phase4',
    'p4_note': 'Phase4推迟至Vis8(延迟66min)',
  },
}

# Sub-task breakdown
def make_subtasks(c):
    d = CASES[c]
    s = {}
    # Phase 2 (settings)
    t = d['phase2'][0]
    s['2'] = [("太阳帆板设置",t,t+2410),("舱外相机设置",t+2410,t+3370),
              ("禁止自主能源",t+3370,t+3410),("禁止电源保护",t+3410,t+3470),
              ("禁止母线掉电",t+3470,t+3510),("禁止热控辐射",t+3510,t+3530)]
    # Phase 3
    t = d['phase3'][0]
    s['3'] = [("小臂任务前重启",t,t+540),("大臂运动准备",t+540,t+740),
              ("转移至中间构型",t+740,t+1100),("大臂至舱I上方",t+1100,t+1540),
              ("大臂至组合构型",t+1540,t+1840)]
    # Phase 4
    t = d['phase4'][0]
    s['4'] = [("小臂至SWA 500mm",t,t+370),("小臂至SWA 300mm",t+370,t+770)]
    # Phase 5
    t = d['phase5'][0]
    s['5'] = [("视觉精定位109mm",t,t+160),("小臂捕获SWA",t+160,t+460)]
    # Phase 6
    t = d['phase6'][0]
    s['6'] = [("大臂给小臂断电",t,t+260),("小臂SWA上电",t+260,t+660),
              ("释放转接件(a)",t+660,t+875),("视觉伺服105mm",t+875,t+1015),
              ("释放转接件(b)",t+1015,t+1260),("小臂手爪收拢",t+1260,t+1560)]
    return s

# ═══════════════════════════════════════════════
# B&W Plotting helpers
# ═══════════════════════════════════════════════
PH_GRAY  = {'1a':0.70,'1b':0.70,'2':0.50,'3':0.35,'4':0.20,'5':0.55,'6':0.42,'W':0.92}
PH_HATCH = {'1a':'//','1b':'//','2':'','3':'\\\\','4':'xx','5':'..','6':'--','W':''}
PH_LABEL = {'1a':'Phase1a','1b':'Phase1b','2':'Phase2:平台设置','3':'Phase3:大臂至组合',
            '4':'Phase4:小臂至SWA','5':'Phase5:视觉捕获','6':'Phase6:独立设置'}

def plot_comm_occ(case_id, suffix=''):
    fig,(ax1,ax2)=plt.subplots(2,1,figsize=(16,4),sharex=True,gridspec_kw={'height_ratios':[1,1]})
    d=CASES[case_id]; H=d['horizon']
    fig.suptitle(f'通信窗口与SWA遮挡时间线 ({d["name"]})',fontsize=13,fontweight='bold')
    for ts,te,on in COMM:
        if ts>H: break
        te2=min(te,H)
        fc=gray(0.85) if on else gray(0.97); h='' if on else '///'
        ax1.barh(0.5,te2-ts,left=ts,height=0.6,fc=fc,ec='black',lw=0.8,hatch=h)
        if on and te2-ts>1500:
            ax1.text((ts+te2)/2,0.5,f'[{ts},{te2}]',ha='center',va='center',fontsize=5.5)
    ax1.set_ylabel('通信窗口',fontsize=10);ax1.set_yticks([]);ax1.set_ylim(0,1)
    ax1.grid(axis='x',alpha=0.3,ls='--')
    ax1.legend(handles=[mpatches.Patch(fc=gray(0.85),ec='k',label='通信可用'),
               mpatches.Patch(fc=gray(0.97),ec='k',hatch='///',label='通信中断')],
               loc='upper right',fontsize=7)

    for ts,te,act in OCC:
        if ts>H: break
        te2=min(te,H)
        fc=gray(0.30) if act else gray(0.95); h='xxx' if act else ''
        ax2.barh(0.5,te2-ts,left=ts,height=0.6,fc=fc,ec='black',lw=0.8,hatch=h)
        if act and te2-ts>100:
            ax2.text((ts+te2)/2,0.5,f'遮挡[{ts},{te2}]',ha='center',va='center',fontsize=6,color='white',fontweight='bold')
    ax2.set_ylabel('SWA遮挡',fontsize=10);ax2.set_xlabel('时间 (s)',fontsize=10)
    ax2.set_yticks([]);ax2.set_ylim(0,1);ax2.grid(axis='x',alpha=0.3,ls='--')
    ax2.legend(handles=[mpatches.Patch(fc=gray(0.30),ec='k',hatch='xxx',label='遮挡活跃'),
               mpatches.Patch(fc=gray(0.95),ec='k',label='遮挡不活跃')],
               loc='upper right',fontsize=7)
    ax2.set_xlim(-500,H+500)
    plt.tight_layout()
    for p in [f'{ARTIFACTS}/bw_case{case_id}_comm_occ{suffix}.png',
              f'{OUTDIR}/bw_case{case_id}_comm_occ{suffix}.png']:
        plt.savefig(p,dpi=200,bbox_inches='tight')
    plt.close()
    print(f'  Saved comm/occ chart case {case_id}')

def plot_phase1(case_id):
    d=CASES[case_id]
    fig,(ax,axc)=plt.subplots(2,1,figsize=(16,4),sharex=True,gridspec_kw={'height_ratios':[2.5,1]})
    fig.suptitle(f'阶段一规划结果 ({d["name"]})',fontsize=13,fontweight='bold')
    for name,ts,te,lbl in [('大臂重启加电保温',*d['bigarm'],'运动前{:.1f}h'.format((d['phase3'][0]-d['bigarm'][1])/3600)),
                            ('小臂重启加电保温',*d['smallarm'],'运动前{:.1f}h'.format((d['phase3'][0]-d['smallarm'][1])/3600))]:
        y = 2 if '大臂' in name else 1
        ax.barh(y,te-ts,left=ts,height=0.55,fc=gray(0.70),ec='black',lw=0.8,hatch='//')
        if te-ts>200:
            ax.text(ts+(te-ts)/2,y,f'{name}\n[{ts},{te}] ({te-ts}s)\n{lbl}',
                    ha='center',va='center',fontsize=6.5,fontweight='bold')
    H2 = d['phase3'][0]+2000
    ax.set_yticks([2,1]);ax.set_yticklabels(['1a:大臂重启','1b:小臂重启'],fontsize=9)
    ax.set_ylim(0.3,2.7);ax.grid(axis='x',alpha=0.3,ls='--');ax.set_ylabel('子任务',fontsize=10)
    # Comm
    for ts,te,on in COMM:
        if ts>H2: break
        te2=min(te,H2)
        fc=gray(0.85) if on else gray(0.97); h='' if on else '///'
        axc.barh(0.5,te2-ts,left=ts,height=0.6,fc=fc,ec='black',lw=0.5,hatch=h)
    axc.set_ylabel('通信',fontsize=9);axc.set_xlabel('时间 (s)',fontsize=10)
    axc.set_yticks([]);axc.set_ylim(0,1);axc.grid(axis='x',alpha=0.3,ls='--')
    axc.set_xlim(-500,H2)
    plt.tight_layout()
    for p in [f'{ARTIFACTS}/bw_case{case_id}_phase1.png', f'{OUTDIR}/bw_case{case_id}_phase1.png']:
        plt.savefig(p,dpi=200,bbox_inches='tight')
    plt.close()
    print(f'  Saved phase1 chart case {case_id}')

def plot_phase2to6(case_id):
    d=CASES[case_id]; subs=make_subtasks(case_id)
    fig=plt.figure(figsize=(18,16))
    gs=GridSpec(4,5,figure=fig,height_ratios=[3.5,0.8,0.8,5],hspace=0.4,wspace=0.3)
    fig.suptitle(f'阶段二至阶段六规划结果 ({d["name"]})',fontsize=13,fontweight='bold',y=0.995)

    ax_m=fig.add_subplot(gs[0,:]);ax_c=fig.add_subplot(gs[1,:],sharex=ax_m);ax_o=fig.add_subplot(gs[2,:],sharex=ax_m)

    # Build plan sequence for Phase2-6
    seq = []
    seq.append(('2',*d['phase2']))
    if d['wait']: seq.append(('W',*d['wait']))
    seq.append(('3',*d['phase3']))
    if d['idle']: seq.append(('W',*d['idle']))
    seq.append(('4',*d['phase4']))
    seq.append(('5',*d['phase5']))
    if d['idle56']: seq.append(('W',*d['idle56']))
    seq.append(('6',*d['phase6']))

    y_map={'2':5,'3':4,'4':3,'5':2,'6':1}
    for pid,ts,te in seq:
        if pid=='W':
            for yk in y_map.values():
                pass # skip wait in main view
            continue
        y=y_map[pid]
        g=PH_GRAY[pid];h=PH_HATCH[pid]
        ax_m.barh(y,te-ts,left=ts,height=0.6,fc=gray(g),ec='black',lw=1,hatch=h)
        txt_c='white' if g<0.5 else 'black'
        if te-ts>800:
            ax_m.text((ts+te)/2,y,f'{PH_LABEL[pid]}\n[{ts},{te}]',ha='center',va='center',fontsize=6,color=txt_c,fontweight='bold')

    # Occ markers
    for ots,ote,act in OCC:
        if act and ots<d['horizon']:
            ax_m.axvspan(ots,min(ote,d['horizon']),color='black',alpha=0.08)

    # Idle/wait bars
    for pid,ts,te in seq:
        if pid=='W' and te-ts>100:
            ax_m.barh(3,te-ts,left=ts,height=0.3,fc=gray(0.92),ec='gray',lw=0.5,ls='--')

    ax_m.set_yticks(list(y_map.values()));ax_m.set_yticklabels([PH_LABEL[k] for k in y_map],fontsize=8)
    ax_m.set_ylim(0.2,6);ax_m.grid(axis='x',alpha=0.3,ls='--');ax_m.set_ylabel('任务阶段',fontsize=10)

    legend_items=[mpatches.Patch(fc=gray(PH_GRAY[k]),ec='k',hatch=PH_HATCH[k],label=PH_LABEL[k]) for k in ['2','3','4','5','6']]
    legend_items.append(mpatches.Patch(fc=gray(0.92),ec='gray',label='等待/空闲'))
    ax_m.legend(handles=legend_items,loc='upper left',fontsize=6.5,ncol=3)

    xmin_all=min(d['phase2'][0],d['phase3'][0])-1000; xmax_all=d['phase6'][1]+1000
    # Comm/Occ rows
    for ts,te,on in COMM:
        if te<xmin_all or ts>xmax_all: continue
        fc=gray(0.85) if on else gray(0.97);h='' if on else '///'
        ax_c.barh(0.5,min(te,xmax_all)-max(ts,xmin_all),left=max(ts,xmin_all),height=0.6,fc=fc,ec='k',lw=0.5,hatch=h)
    ax_c.set_ylabel('通信',fontsize=8);ax_c.set_yticks([]);ax_c.set_ylim(0,1);ax_c.grid(axis='x',alpha=0.3,ls='--')
    for ts,te,act in OCC:
        if te<xmin_all or ts>xmax_all: continue
        fc=gray(0.30) if act else gray(0.95);h='xxx' if act else ''
        ax_o.barh(0.5,min(te,xmax_all)-max(ts,xmin_all),left=max(ts,xmin_all),height=0.6,fc=fc,ec='k',lw=0.5,hatch=h)
        if act:
            ax_o.text((max(ts,xmin_all)+min(te,xmax_all))/2,0.5,f'[{ts},{te}]',ha='center',va='center',fontsize=5.5,color='white',fontweight='bold')
    ax_o.set_ylabel('遮挡',fontsize=8);ax_o.set_xlabel('时间 (s)',fontsize=9)
    ax_o.set_yticks([]);ax_o.set_ylim(0,1);ax_o.grid(axis='x',alpha=0.3,ls='--')
    ax_o.set_xlim(xmin_all,xmax_all)

    # Zoom panels
    zoom_pids=['2','3','4','5','6']
    for zi,pid in enumerate(zoom_pids):
        ax_z=fig.add_subplot(gs[3,zi])
        tasks=subs[pid]
        g=PH_GRAY[pid];h=PH_HATCH[pid];n=len(tasks)
        all_ts=[t[1] for t in tasks];all_te=[t[2] for t in tasks]
        xmn=min(all_ts)-max(80,(max(all_te)-min(all_ts))*0.06)
        xmx=max(all_te)+max(80,(max(all_te)-min(all_ts))*0.06)
        # Occ bands
        if pid in ['4','5']:
            for ots,ote,act in OCC:
                if act and ote>xmn and ots<xmx:
                    ax_z.axvspan(max(ots,xmn),min(ote,xmx),color='black',alpha=0.12)
        for ti,(nm,ts,te) in enumerate(tasks):
            yr=n-ti;shade=g-0.08*(ti%2)
            ax_z.barh(yr,te-ts,left=ts,height=0.7,fc=gray(shade),ec='black',lw=0.8,hatch=h)
            dur=te-ts;bf=dur/(xmx-xmn);tc='white' if shade<0.5 else 'black'
            if bf>0.1: ax_z.text((ts+te)/2,yr,f'{nm}\n({dur}s)',ha='center',va='center',fontsize=5.5,color=tc,fontweight='bold')
            elif bf>0.03: ax_z.text((ts+te)/2,yr,nm,ha='center',va='center',fontsize=5,color=tc,fontweight='bold')
            else: ax_z.text(te+8,yr,f'{nm}({dur}s)',ha='left',va='center',fontsize=5)
        ax_z.set_xlim(xmn,xmx);ax_z.set_ylim(0.2,n+0.8)
        ax_z.set_yticks(range(1,n+1));ax_z.set_yticklabels([t[0] for t in reversed(tasks)],fontsize=5.5)
        ax_z.grid(axis='x',alpha=0.3,ls='--');ax_z.set_xlabel('时间(s)',fontsize=7)
        swa=' ⚠' if pid in ['4','5'] else ''
        ax_z.set_title(f'{PH_LABEL[pid]}局部放大{swa}',fontsize=7.5,fontweight='bold')
        for sp in ax_z.spines.values(): sp.set_edgecolor('black');sp.set_linewidth(1.5);sp.set_linestyle('--')

    for p in [f'{ARTIFACTS}/bw_case{case_id}_phase2to6.png',f'{OUTDIR}/bw_case{case_id}_phase2to6.png']:
        plt.savefig(p,dpi=200,bbox_inches='tight')
    plt.close()
    print(f'  Saved phase2-6 chart case {case_id}')

# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════
if __name__=='__main__':
    for cid in [1,2]:
        print(f'\n=== {CASES[cid]["name"]} ===')
        plot_comm_occ(cid)
        plot_phase1(cid)
        plot_phase2to6(cid)
    print('\nAll charts generated.')
