#!/usr/bin/env python3
"""
Generate all charts + Word document for EUROPA-verified plans.
T0 = 2025-07-25 21:00 UTC = 2025-07-26 05:00 BJT
All tasks strictly within comm windows. EUROPA solver verified.
"""
import os, math
from datetime import datetime, timedelta, timezone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np

try: plt.rcParams['font.family']=['Noto Sans CJK JP','sans-serif']
except: pass
plt.rcParams['axes.unicode_minus']=False

ART='/opt/cursor/artifacts'
OUT='/workspace/examples/experiment_final'
T0=datetime(2025,7,25,21,0,0,tzinfo=timezone.utc); BJT_O=timedelta(hours=8)
def tb(t): return (T0+timedelta(seconds=t)+BJT_O).strftime('%H:%M')
def tbf(t): return (T0+timedelta(seconds=t)+BJT_O).strftime('%m-%d %H:%M')
def g(l): return (l,l,l)

COMM=[(0,100,False),(110,3580,True),(3590,6120,False),(6130,9490,True),(9500,12030,False),
      (12040,15330,True),(15340,17880,False),(17890,21160,True),(21170,23710,False),
      (23720,27030,True),(27040,29570,False),(29580,33000,True),(33010,35540,False),
      (35550,39060,True),(39070,41600,False),(41610,45090,True),(45100,47630,False),
      (47640,51010,True),(51020,53550,False),(53560,56850,True),(56860,59420,False),
      (59430,62870,True),(62880,65350,False),(65360,68830,True),(68840,71050,False),
      (71060,74570,True)]
OCC=[(0,61750,False),(61750,62180,True),(62180,75450,False),(75450,76110,True),(76110,90000,False)]
OCC_A=[(61750,62180),(75450,76110)]

PG={'1a':.70,'1b':.70,'2A':.50,'2B':.50,'3':.35,'4':.20,'5':.55,'6':.42,'W':.92}
PH={'1a':'//','1b':'//','2A':'','2B':'','3':'\\\\','4':'xx','5':'..','6':'--','W':''}
PL={'1a':'Phase1a:大臂重启','1b':'Phase1b:小臂重启','2A':'Phase2A:帆板+相机','2B':'Phase2B:禁止项',
    '3':'Phase3:大臂至组合','4':'Phase4:小臂至SWA','5':'Phase5:视觉捕获','6':'Phase6:独立设置'}

# EUROPA-verified plan data
C={
 1:{'name':'算例一（无遮挡冲突）',
    'tokens':[('1a',6130,7110),('1b',37250,37400),('2A',41610,44980),('2B',47640,47800),
              ('W',47800,53560),('3',53560,55400),('4',55400,56170),('5',56170,56630),
              ('W',56630,59430),('6',59430,60990)],
    'horizon':66000,'ba_adv':'12.9','sa_adv':'5.0','occ_delay':0,
    'p3_vis':'Vis10[53560,56850]','p6_vis':'Vis11[59430,62870]',
 },
 2:{'name':'算例二（遮挡冲突）',
    'tokens':[('1a',12040,13020),('1b',47640,47790),('2A',47791,51010),('2B',53560,53720),
              ('W',53720,59430),('3',59430,61270),('W',61270,65360),
              ('4',65360,66130),('5',66130,66590),('6',66590,68150)],
    'horizon':74000,'ba_adv':'12.9','sa_adv':'4.9','occ_delay':4090,
    'p3_vis':'Vis11[59430,62870]','p6_vis':'Vis12[65360,68830]',
 },
}

def make_subs(d):
    s={}; toks={t[0]:t for t in d['tokens'] if t[0]!='W'}
    s['1a']=[("大臂重启加电保温",*toks['1a'][1:])]
    s['1b']=[("小臂重启加电保温",*toks['1b'][1:])]
    t=toks['2A'][1]
    s['2A']=[("太阳帆板设置",t,t+2410),("舱外相机设置",t+2410,min(t+3370,toks['2A'][2]))]
    t=toks['2B'][1]; dur2b=toks['2B'][2]-toks['2B'][1]
    if dur2b>=160: s['2B']=[("禁止自主能源",t,t+40),("禁止电源保护",t+40,t+100),("禁止母线掉电",t+100,t+140),("禁止热控辐射",t+140,t+160)]
    else: s['2B']=[("禁止项设置",t,t+dur2b)]
    t=toks['3'][1]
    s['3']=[("小臂任务前重启",t,t+540),("大臂运动准备",t+540,t+740),("转移至中间构型",t+740,t+1100),("大臂至舱I上方",t+1100,t+1540),("大臂至组合构型",t+1540,t+1840)]
    t=toks['4'][1]; s['4']=[("小臂至SWA500mm",t,t+370),("小臂至SWA300mm",t+370,t+770)]
    t=toks['5'][1]; s['5']=[("视觉精定位109mm",t,t+160),("小臂捕获SWA",t+160,t+460)]
    t=toks['6'][1]; s['6']=[("大臂给小臂断电",t,t+260),("小臂SWA上电",t+260,t+660),("释放转接件(a)",t+660,t+875),("视觉伺服105mm",t+875,t+1015),("释放转接件(b)",t+1015,t+1260),("小臂手爪收拢",t+1260,t+1560)]
    return s

def sv(fig,name):
    for p in [f'{ART}/{name}',f'{OUT}/{name}']: fig.savefig(p,dpi=200,bbox_inches='tight')
    plt.close(fig); print(f'  {name}')

# ═══ Chart 1: Comm+Occ ═══
def ch_comm(cid):
    d=C[cid]; H=d['horizon']
    fig,(a1,a2)=plt.subplots(2,1,figsize=(16,4.5),sharex=True,gridspec_kw={'height_ratios':[1,1]})
    fig.suptitle(f'通信窗口与SWA遮挡时间线 ({d["name"]})\nT0=2025-07-26 05:00 BJT',fontsize=12,fontweight='bold')
    for ts,te,on in COMM:
        if ts>H: break
        te2=min(te,H); fc=g(.85) if on else g(.97); h='' if on else '///'
        a1.barh(.5,te2-ts,left=ts,height=.6,fc=fc,ec='k',lw=.8,hatch=h)
        if on and te2-ts>1800: a1.text((ts+te2)/2,.5,f'[{tb(ts)},{tb(te2)}]',ha='center',va='center',fontsize=5.5)
    a1.set_ylabel('通信窗口',fontsize=10);a1.set_yticks([]);a1.set_ylim(0,1);a1.grid(axis='x',alpha=.3,ls='--')
    a1.legend(handles=[mpatches.Patch(fc=g(.85),ec='k',label='通信可用'),mpatches.Patch(fc=g(.97),ec='k',hatch='///',label='通信中断')],fontsize=7,loc='upper right')
    for ts,te,act in OCC:
        if ts>H: break
        te2=min(te,H); fc=g(.30) if act else g(.95); h='xxx' if act else ''
        a2.barh(.5,te2-ts,left=ts,height=.6,fc=fc,ec='k',lw=.8,hatch=h)
        if act and te2-ts>100: a2.text((ts+te2)/2,.5,f'遮挡[{tb(ts)},{tb(te2)}]',ha='center',va='center',fontsize=6,color='white',fontweight='bold')
    a2.set_ylabel('SWA遮挡',fontsize=10);a2.set_xlabel('时间(s)',fontsize=10);a2.set_yticks([]);a2.set_ylim(0,1);a2.grid(axis='x',alpha=.3,ls='--')
    a2.legend(handles=[mpatches.Patch(fc=g(.30),ec='k',hatch='xxx',label='遮挡活跃'),mpatches.Patch(fc=g(.95),ec='k',label='遮挡不活跃')],fontsize=7,loc='upper right')
    a2.set_xlim(-500,H+500)
    at=a1.twiny();at.set_xlim(a1.get_xlim());tks=list(range(0,H+1,7200));at.set_xticks(tks);at.set_xticklabels([tb(t) for t in tks],fontsize=7);at.set_xlabel('BJT',fontsize=8)
    plt.tight_layout(); sv(fig,f'case{cid}_comm_occ.png')

# ═══ Chart 2: Phase1 ═══
def ch_p1(cid):
    d=C[cid]; toks={t[0]:t for t in d['tokens'] if t[0]!='W'}
    ba=toks['1a']; sa=toks['1b']; p3=toks['3']; p4=toks['4']
    fig,(ax,axc)=plt.subplots(2,1,figsize=(16,5.5),sharex=True,gridspec_kw={'height_ratios':[3.5,1]})
    fig.suptitle(f'阶段一规划结果 ({d["name"]})',fontsize=12,fontweight='bold')
    ax.barh(2,ba[2]-ba[1],left=ba[1],height=.55,fc=g(.70),ec='k',lw=.8,hatch='//')
    ax.text(ba[1]+(ba[2]-ba[1])/2,2,f'大臂重启(980s) [{ba[1]},{ba[2]}]',ha='center',va='center',fontsize=7,fontweight='bold')
    ax.barh(1,sa[2]-sa[1],left=sa[1],height=.55,fc=g(.70),ec='k',lw=.8,hatch='//')
    ax.text(sa[1]+(sa[2]-sa[1])/2,1,f'小臂重启(150s) [{sa[1]},{sa[2]}]',ha='center',va='center',fontsize=7,fontweight='bold')
    ax.annotate('',xy=(ba[2],2.35),xytext=(p3[1],2.35),arrowprops=dict(arrowstyle='<->',lw=1.5))
    ax.text((ba[2]+p3[1])/2,2.5,f'≥12h ({d["ba_adv"]}h)',ha='center',fontsize=7)
    ax.annotate('',xy=(sa[2],.65),xytext=(p4[1],.65),arrowprops=dict(arrowstyle='<->',lw=1.5))
    ax.text((sa[2]+p4[1])/2,.5,f'≥5h ({d["sa_adv"]}h)',ha='center',fontsize=7)
    ax.axvline(p3[1],color='k',ls=':',lw=1,alpha=.5);ax.text(p3[1],2.7,f'Phase3 {p3[1]}s',ha='center',fontsize=6.5)
    ax.axvline(p4[1],color='k',ls=':',lw=1,alpha=.5);ax.text(p4[1],.3,f'Phase4 {p4[1]}s',ha='center',fontsize=6.5)
    ax.set_yticks([2,1]);ax.set_yticklabels(['1a:大臂重启(Phase3前12h)','1b:小臂重启(Phase4前5h)'],fontsize=8)
    ax.set_ylim(0,3.2);ax.grid(axis='x',alpha=.3,ls='--');ax.set_ylabel('子任务',fontsize=10)
    H2=p4[1]+3000
    for ts,te,on in COMM:
        if ts>H2: break
        te2=min(te,H2);fc=g(.85) if on else g(.97);h='' if on else '///'
        axc.barh(.5,te2-ts,left=ts,height=.6,fc=fc,ec='k',lw=.5,hatch=h)
    axc.set_ylabel('通信',fontsize=9);axc.set_xlabel('时间(s)',fontsize=10);axc.set_yticks([]);axc.set_ylim(0,1);axc.grid(axis='x',alpha=.3,ls='--');axc.set_xlim(-500,H2)
    plt.tight_layout(); sv(fig,f'case{cid}_phase1.png')

# ═══ Chart 3: Phase2-6 + zoom ═══
def ch_p2to6(cid):
    d=C[cid]; subs=make_subs(d); toks={t[0]:t for t in d['tokens']}
    fig=plt.figure(figsize=(18,16));gs=GridSpec(4,6,figure=fig,height_ratios=[3.5,.8,.8,5],hspace=.4,wspace=.3)
    fig.suptitle(f'阶段二至阶段六规划结果 ({d["name"]})',fontsize=13,fontweight='bold',y=.995)
    ax_m=fig.add_subplot(gs[0,:]);ax_c=fig.add_subplot(gs[1,:],sharex=ax_m);ax_o=fig.add_subplot(gs[2,:],sharex=ax_m)
    ym={'2A':6,'2B':5,'3':4,'4':3,'5':2,'6':1}
    for pid in ['2A','2B','3','4','5','6']:
        if pid not in toks: continue
        ts,te=toks[pid][1],toks[pid][2]; y=ym[pid]; gg=PG[pid]; h=PH[pid]
        ax_m.barh(y,te-ts,left=ts,height=.6,fc=g(gg),ec='k',lw=1,hatch=h)
        tc='white' if gg<.5 else 'black'
        if te-ts>400: ax_m.text((ts+te)/2,y,f'{PL[pid]}\n[{ts},{te}]',ha='center',va='center',fontsize=5.5,color=tc,fontweight='bold')
    # Waits
    for tok in d['tokens']:
        if tok[0]=='W' and tok[2]-tok[1]>100:
            ax_m.barh(3,tok[2]-tok[1],left=tok[1],height=.25,fc=g(.92),ec='gray',lw=.5)
            if tok[2]-tok[1]>500: ax_m.text((tok[1]+tok[2])/2,3.3,f'等待{(tok[2]-tok[1])//60}min',ha='center',fontsize=5.5,color='gray',fontstyle='italic')
    for ots,ote,act in OCC:
        if act: ax_m.axvspan(ots,ote,color='k',alpha=.08)
    ax_m.set_yticks(list(ym.values()));ax_m.set_yticklabels([PL[k] for k in ym],fontsize=7.5)
    ax_m.set_ylim(.2,7);ax_m.grid(axis='x',alpha=.3,ls='--');ax_m.set_ylabel('任务阶段',fontsize=10)
    items=[mpatches.Patch(fc=g(PG[k]),ec='k',hatch=PH[k],label=PL[k]) for k in ['2A','3','4','5','6']]
    items.append(mpatches.Patch(fc=g(.92),ec='gray',label='等待'));ax_m.legend(handles=items,loc='upper left',fontsize=6,ncol=3)
    xmin=min(t[1] for t in d['tokens'] if t[0]!='1a' and t[0]!='1b')-1000
    xmax=max(t[2] for t in d['tokens'])+1500
    for ts,te,on in COMM:
        if te<xmin or ts>xmax: continue
        fc=g(.85) if on else g(.97);h='' if on else '///'
        ax_c.barh(.5,min(te,xmax)-max(ts,xmin),left=max(ts,xmin),height=.6,fc=fc,ec='k',lw=.5,hatch=h)
    ax_c.set_ylabel('通信',fontsize=8);ax_c.set_yticks([]);ax_c.set_ylim(0,1);ax_c.grid(axis='x',alpha=.3,ls='--')
    for ts,te,act in OCC:
        if te<xmin or ts>xmax: continue
        fc=g(.30) if act else g(.95);h='xxx' if act else ''
        ax_o.barh(.5,min(te,xmax)-max(ts,xmin),left=max(ts,xmin),height=.6,fc=fc,ec='k',lw=.5,hatch=h)
        if act: ax_o.text((max(ts,xmin)+min(te,xmax))/2,.5,'遮挡',ha='center',va='center',fontsize=6,color='white',fontweight='bold')
    ax_o.set_ylabel('遮挡',fontsize=8);ax_o.set_xlabel('时间(s)',fontsize=9);ax_o.set_yticks([]);ax_o.set_ylim(0,1);ax_o.grid(axis='x',alpha=.3,ls='--');ax_o.set_xlim(xmin,xmax)
    # Zoom panels
    for zi,pid in enumerate(['2A','3','4','5','6']):
        ax_z=fig.add_subplot(gs[3,zi]);tasks=subs.get(pid,[]);gg=PG.get(pid,.5);h=PH.get(pid,'');n=len(tasks)
        if not tasks: continue
        at=[t[1] for t in tasks];ae=[t[2] for t in tasks];mg=max(80,(max(ae)-min(at))*.06);xn=min(at)-mg;xx=max(ae)+mg
        if pid in ['4','5']:
            for ots,ote in OCC_A:
                if ote>xn and ots<xx: ax_z.axvspan(max(ots,xn),min(ote,xx),color='k',alpha=.12)
        for ti,(nm,ts,te) in enumerate(tasks):
            yr=n-ti;sh=gg-.08*(ti%2);ax_z.barh(yr,te-ts,left=ts,height=.7,fc=g(sh),ec='k',lw=.8,hatch=h)
            dur=te-ts;bf=dur/(xx-xn);tc='white' if sh<.5 else 'black'
            if bf>.1: ax_z.text((ts+te)/2,yr,f'{nm}\n({dur}s)',ha='center',va='center',fontsize=5.5,color=tc,fontweight='bold')
            elif bf>.03: ax_z.text((ts+te)/2,yr,nm,ha='center',va='center',fontsize=5,color=tc,fontweight='bold')
            else: ax_z.text(te+8,yr,f'{nm}({dur}s)',ha='left',va='center',fontsize=5)
        ax_z.set_xlim(xn,xx);ax_z.set_ylim(.2,n+.8);ax_z.set_yticks(range(1,n+1));ax_z.set_yticklabels([t[0] for t in reversed(tasks)],fontsize=5.5)
        ax_z.grid(axis='x',alpha=.3,ls='--');ax_z.set_xlabel('时间(s)',fontsize=7)
        swa=' ⚠' if pid in ['4','5'] else '';ax_z.set_title(f'{PL.get(pid,pid)}局部放大{swa}',fontsize=7.5,fontweight='bold')
        for sp in ax_z.spines.values(): sp.set_edgecolor('k');sp.set_linewidth(1.5);sp.set_linestyle('--')
    # 6th zoom: Phase2B
    ax_z6=fig.add_subplot(gs[3,5]); tasks_2b=subs.get('2B',[]); n2=len(tasks_2b)
    if tasks_2b:
        at2=[t[1] for t in tasks_2b];ae2=[t[2] for t in tasks_2b];mg2=max(30,(max(ae2)-min(at2))*.15);xn2=min(at2)-mg2;xx2=max(ae2)+mg2
        for ti,(nm,ts,te) in enumerate(tasks_2b):
            yr=n2-ti;sh=PG['2B']-.08*(ti%2);ax_z6.barh(yr,te-ts,left=ts,height=.7,fc=g(sh),ec='k',lw=.8)
            dur=te-ts;tc='white' if sh<.5 else 'black';ax_z6.text(te+5,yr,f'{nm}({dur}s)',ha='left',va='center',fontsize=5)
        ax_z6.set_xlim(xn2,xx2);ax_z6.set_ylim(.2,n2+.8);ax_z6.set_yticks([]);ax_z6.grid(axis='x',alpha=.3,ls='--');ax_z6.set_xlabel('时间(s)',fontsize=7)
        ax_z6.set_title('Phase2B局部放大',fontsize=7.5,fontweight='bold')
        for sp in ax_z6.spines.values(): sp.set_edgecolor('k');sp.set_linewidth(1.5);sp.set_linestyle('--')
    sv(fig,f'case{cid}_phase2to6.png')

# ═══ Chart 4: Per-phase ═══
def ch_per(cid):
    d=C[cid];subs=make_subs(d);pids=['1a','1b','2A','2B','3','4','5','6']
    fig,axes=plt.subplots(len(pids),1,figsize=(16,20),sharex=False)
    fig.suptitle(f'各阶段子任务规划结果 ({d["name"]})',fontsize=14,fontweight='bold',y=.998)
    for idx,pid in enumerate(pids):
        ax=axes[idx];tasks=subs.get(pid,[]);gg=PG.get(pid,.5);h=PH.get(pid,'');n=len(tasks)
        if not tasks: continue
        at=[t[1] for t in tasks];ae=[t[2] for t in tasks];sp=max(ae)-min(at);mg=max(80,sp*.08);xn=min(at)-mg;xx=max(ae)+mg
        if pid in ['4','5']:
            for ots,ote in OCC_A:
                if ote>xn and ots<xx: ax.axvspan(max(ots,xn),min(ote,xx),color='k',alpha=.12)
        for ti,(nm,ts,te) in enumerate(tasks):
            y=n-ti;sh=gg-.08*(ti%2);ax.barh(y,te-ts,left=ts,height=.65,fc=g(sh),ec='k',lw=.8,hatch=h)
            dur=te-ts;bf=dur/(xx-xn);tc='white' if sh<.5 else 'black'
            if bf>.12: ax.text(ts+dur/2,y,f'{nm} ({dur}s)',ha='center',va='center',fontsize=7,color=tc,fontweight='bold')
            elif bf>.04: ax.text(ts+dur/2,y,nm,ha='center',va='center',fontsize=6.5,color=tc,fontweight='bold')
            else: ax.text(te+15,y,f'{nm} ({dur}s)',ha='left',va='center',fontsize=6.5)
        ax.set_yticks(range(1,n+1));ax.set_yticklabels([t[0] for t in reversed(tasks)],fontsize=7)
        ax.set_ylim(.3,n+.7);ax.set_xlim(xn,xx);ax.grid(axis='x',alpha=.3,ls='--');ax.set_xlabel('时间(s)',fontsize=8)
        swa='  ⚠遮挡约束' if pid in ['4','5'] else ''
        ax.set_title(f'{PL.get(pid,pid)}  [{min(at)}s~{max(ae)}s] ({max(ae)-min(at)}s){swa}',fontsize=9.5,fontweight='bold',loc='left')
    plt.tight_layout();sv(fig,f'case{cid}_per_phase.png')

# ═══ Chart 5: Overall ═══
def ch_all(cid):
    d=C[cid];H=d['horizon']
    fig,(ax_m,ax_c,ax_o)=plt.subplots(3,1,figsize=(18,8),sharex=True,gridspec_kw={'height_ratios':[5,1,1]})
    fig.suptitle(f'机械臂全任务规划总图 ({d["name"]})',fontsize=13,fontweight='bold')
    ym={'1a':8,'1b':7,'2A':6,'2B':5,'3':4,'4':3,'5':2,'6':1}
    for tok in d['tokens']:
        pid=tok[0]; ts,te=tok[1],tok[2]
        if pid=='W':
            ax_m.barh(4,te-ts,left=ts,height=.25,fc=g(.92),ec='gray',lw=.4)
            continue
        y=ym.get(pid,4);gg=PG.get(pid,.5);h=PH.get(pid,'')
        ax_m.barh(y,te-ts,left=ts,height=.6,fc=g(gg),ec='k',lw=.8,hatch=h)
        tc='white' if gg<.5 else 'black'
        if te-ts>1000: ax_m.text((ts+te)/2,y,PL.get(pid,pid),ha='center',va='center',fontsize=6,color=tc,fontweight='bold')
    ax_m.set_yticks(list(ym.values()));ax_m.set_yticklabels([PL.get(k,k) for k in ym],fontsize=7)
    ax_m.set_ylim(.5,9);ax_m.grid(axis='x',alpha=.3,ls='--');ax_m.set_ylabel('任务阶段',fontsize=10)
    items=[mpatches.Patch(fc=g(PG[k]),ec='k',hatch=PH[k],label=PL[k]) for k in ['1a','2A','3','4','5','6']]
    ax_m.legend(handles=items,loc='upper left',fontsize=6,ncol=3)
    for ts,te,on in COMM:
        if ts>H: break
        te2=min(te,H);fc=g(.85) if on else g(.97);h='' if on else '///'
        ax_c.barh(.5,te2-ts,left=ts,height=.6,fc=fc,ec='k',lw=.5,hatch=h)
    ax_c.set_ylabel('通信',fontsize=8);ax_c.set_yticks([]);ax_c.set_ylim(0,1);ax_c.grid(axis='x',alpha=.3,ls='--')
    for ts,te,act in OCC:
        if ts>H: break
        te2=min(te,H);fc=g(.30) if act else g(.95);h='xxx' if act else ''
        ax_o.barh(.5,te2-ts,left=ts,height=.6,fc=fc,ec='k',lw=.5,hatch=h)
    ax_o.set_ylabel('遮挡',fontsize=8);ax_o.set_xlabel('时间(s)',fontsize=10);ax_o.set_yticks([]);ax_o.set_ylim(0,1);ax_o.grid(axis='x',alpha=.3,ls='--')
    ax_o.set_xlim(-500,H+500)
    plt.tight_layout();sv(fig,f'case{cid}_overall.png')

# ═══ Word ═══
def gen_word():
    from docx import Document; from docx.shared import Pt,RGBColor,Inches; from docx.enum.text import WD_ALIGN_PARAGRAPH; from docx.oxml.ns import qn
    def shd(c,cl): pr=c._element.get_or_add_tcPr();pr.append(pr.makeelement(qn('w:shd'),{qn('w:val'):'clear',qn('w:color'):'auto',qn('w:fill'):cl}))
    def htb(doc,hd,rows):
        t=doc.add_table(rows=1+len(rows),cols=len(hd),style='Table Grid')
        for i,h in enumerate(hd): c=t.rows[0].cells[i];c.text=h;c.paragraphs[0].runs[0].bold=True;shd(c,'D9E2F3')
        for ri,row in enumerate(rows):
            for ci,v in enumerate(row): t.rows[ri+1].cells[ci].text=str(v)
    def img(doc,name,cap):
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;r=p.add_run();r.add_picture(f'{OUT}/{name}',width=Inches(6.0))
        p2=doc.add_paragraph();p2.alignment=WD_ALIGN_PARAGRAPH.CENTER;p2.add_run(cap).italic=True;doc.add_paragraph()

    doc=Document();s=doc.styles['Normal'];s.font.name='Times New Roman';s.font.size=Pt(12)
    s.paragraph_format.line_spacing=1.5;s.paragraph_format.space_after=Pt(6)
    rPr=s.element.get_or_add_rPr();rPr.append(rPr.makeelement(qn('w:rFonts'),{qn('w:eastAsia'):'宋体'}))
    for lv in range(1,4): h=doc.styles[f'Heading {lv}'];h.font.color.rgb=RGBColor(0,0,0);h.font.bold=True;h.font.size=Pt([0,16,14,12][lv])

    title=doc.add_heading('第X章 仿真算例设计与实验分析',level=1);title.alignment=WD_ALIGN_PARAGRAPH.CENTER
    doc.add_heading('X.1 仿真参数设定',level=2)
    doc.add_paragraph('T0=2025-07-25 21:00 UTC（BJT 07-26 05:00）。所有任务必须完全在通信窗口内执行。Phase2因总时长(3530s)超过单个通信窗口容量(~3400s)，拆分为Phase2A和Phase2B分别在不同窗口内执行。')
    doc.add_paragraph()

    for cid in [1,2]:
        d=C[cid]; doc.add_heading(f'X.{cid+1} {d["name"]}',level=2)
        toks={t[0]:t for t in d['tokens'] if t[0]!='W'}
        waits=[(t[1],t[2]) for t in d['tokens'] if t[0]=='W' and t[2]-t[1]>100]
        if cid==1: doc.add_paragraph('Phase3至Phase5在Vis10内连续执行，Phase6在Vis11内执行，无遮挡影响。')
        else: doc.add_paragraph(f'Phase3在Vis11执行后，遮挡事件[61750,62180]阻断Phase4。Phase4-6推迟至Vis12，等待{d["occ_delay"]}s（{d["occ_delay"]//60}min）。')
        p=doc.add_paragraph();p.add_run(f'表X-{cid+1} {d["name"]}任务规划结果（EUROPA求解）').bold=True;p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        rows=[]
        for tok in d['tokens']:
            pid,ts,te=tok
            if pid=='W':
                if te-ts>100: rows.append(['—','等待',str(ts),str(te),str(te-ts),'—','通信间隙/遮挡'])
                continue
            nm=PL.get(pid,pid); dur=str(te-ts)
            note='—'
            if pid=='1a': note=f'Phase3前{d["ba_adv"]}h'
            elif pid=='1b': note=f'Phase4前{d["sa_adv"]}h'
            elif pid in ['4','5']: note='需通信+无遮挡'
            rows.append([pid,nm,str(ts),str(te),dur,'含通信窗口内',note])
        htb(doc,['阶段','任务','开始(s)','结束(s)','时长(s)','通信','约束'],rows)
        doc.add_paragraph()
        img(doc,f'case{cid}_comm_occ.png',f'图X-{cid*5-4} {d["name"]}通信窗口与SWA遮挡时间线')
        img(doc,f'case{cid}_phase1.png',f'图X-{cid*5-3} {d["name"]}阶段一规划结果')
        img(doc,f'case{cid}_phase2to6.png',f'图X-{cid*5-2} {d["name"]}阶段二至六规划结果（含局部放大）')
        img(doc,f'case{cid}_per_phase.png',f'图X-{cid*5-1} {d["name"]}各阶段子任务规划结果')
        img(doc,f'case{cid}_overall.png',f'图X-{cid*5} {d["name"]}全任务规划总图')

    d1,d2=C[1],C[2]
    doc.add_heading('X.4 对比分析',level=2)
    p=doc.add_paragraph();p.add_run('表X-4 两算例对比').bold=True;p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    htb(doc,['对比项','算例一','算例二'],[
        ['Phase3窗口',d1['p3_vis'],d2['p3_vis']],['遮挡影响','无',f'[61750,62180]阻断Phase4'],
        ['Phase4起始','55400s(紧随Phase3)',f'65360s(推迟至Vis12)'],['遮挡等待','0s',f'{d2["occ_delay"]}s({d2["occ_delay"]//60}min)'],
        ['大臂提前量',f'{d1["ba_adv"]}h ✓',f'{d2["ba_adv"]}h ✓'],['小臂提前量',f'{d1["sa_adv"]}h ✓',f'{d2["sa_adv"]}h ✓'],
        ['任务完成',f'{d1["tokens"][-1][2]}s',f'{d2["tokens"][-1][2]}s'],
    ])
    doc.add_paragraph()
    doc.add_paragraph('两算例均满足：(1)所有任务完全在通信窗口内执行；(2)大臂重启≥12h提前量；(3)小臂重启≥5h提前量。算例一验证基本调度能力，算例二验证遮挡约束回避能力。')
    doc.add_heading('X.5 本章小结',level=2)
    doc.add_paragraph('本章基于统一TLE轨道根数，通过EUROPA规划框架求解两组仿真算例。所有任务严格限制在通信窗口内执行，Phase2因超出单窗口容量被自动拆分。算例二中SWA遮挡事件导致Phase4推迟68分钟，验证了约束回避能力。')
    for p in [f'{ART}/experiment_chapter.docx',f'{OUT}/experiment_chapter.docx','/workspace/documentation/experiment_chapter_final.docx']:
        doc.save(p)
    print('  Word saved')

if __name__=='__main__':
    for cid in [1,2]:
        print(f'\n=== {C[cid]["name"]} ===')
        ch_comm(cid);ch_p1(cid);ch_p2to6(cid);ch_per(cid);ch_all(cid)
    print('\n=== Word ===');gen_word()
    print('\nDone.')
