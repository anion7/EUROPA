#!/usr/bin/env python3
"""
Generate Word document: Modeling Chapter for Space Station Robotic Arm
Task Planning — formal problem definition, Timeline modeling, constraint
formalization, and NDDL encoding.
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn

def shading(cell, color):
    pr = cell._element.get_or_add_tcPr()
    el = pr.makeelement(qn('w:shd'), {qn('w:val'):'clear',qn('w:color'):'auto',qn('w:fill'):color})
    pr.append(el)

def htable(doc, headers, rows, shade='D9E2F3'):
    t = doc.add_table(rows=1+len(rows), cols=len(headers), style='Table Grid')
    for i,h in enumerate(headers):
        c=t.rows[0].cells[i]; c.text=h; c.paragraphs[0].runs[0].bold=True; shading(c,shade)
    for ri,row in enumerate(rows):
        for ci,v in enumerate(row): t.rows[ri+1].cells[ci].text=str(v)
    return t

def code(doc, txt):
    for ln in txt.strip().split('\n'):
        p=doc.add_paragraph(); p.style=doc.styles['code']; p.add_run(ln)

def bold_run(p, text):
    r=p.add_run(text); r.bold=True; return r

def italic_run(p, text):
    r=p.add_run(text); r.italic=True; return r

def formula(doc, text):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    italic_run(p, text); return p

def create():
    doc=Document()
    # styles
    s=doc.styles['Normal']; s.font.name='Times New Roman'; s.font.size=Pt(12)
    s.paragraph_format.line_spacing=1.5; s.paragraph_format.space_after=Pt(6)
    rPr=s.element.get_or_add_rPr()
    rPr.append(rPr.makeelement(qn('w:rFonts'),{qn('w:eastAsia'):'宋体'}))
    for lv in range(1,4):
        h=doc.styles[f'Heading {lv}']; h.font.color.rgb=RGBColor(0,0,0); h.font.bold=True
        h.font.size=Pt([0,16,14,12][lv])
    cs=doc.styles.add_style('code',WD_STYLE_TYPE.PARAGRAPH)
    cs.font.name='Consolas'; cs.font.size=Pt(9)
    cs.paragraph_format.space_before=Pt(0); cs.paragraph_format.space_after=Pt(0)
    cs.paragraph_format.line_spacing=1.15; cs.paragraph_format.left_indent=Cm(1)

    # ════════════════════════════════════════
    title=doc.add_heading('第X章 机械臂作业规划建模',level=1)
    title.alignment=WD_ALIGN_PARAGRAPH.CENTER

    # ────────────────────────────────────────
    doc.add_heading('X.1 问题概述',level=2)

    doc.add_paragraph(
        '空间站机械臂在轨作业任务规划问题可抽象为一类带时序约束和资源约束的调度问题。'
        '机械臂需执行一系列预定义的操作子任务，每个子任务具有固定的持续时间和严格的执行顺序。'
        '任务执行过程受到两类环境约束的限制：其一，所有操作必须在地面测控站或中继卫星提供的通信可见窗口内完成；'
        '其二，当机械臂在特定工位（如SWA转位机构）附近作业时，臂杆可能遮挡空间站天线与中继卫星之间的通信链路，'
        '此时须回避遮挡区间。上述问题的核心挑战在于通信窗口的周期性中断与遮挡约束的空间耦合，'
        '要求规划算法在满足所有约束的前提下确定各子任务的可行执行时间。'
    )

    # ────────────────────────────────────────
    doc.add_heading('X.2 形式化问题定义',level=2)

    doc.add_heading('X.2.1 规划问题的数学表述',level=3)

    doc.add_paragraph('将机械臂作业规划问题形式化定义为一个约束满足问题（CSP）：')

    formula(doc, 'P = ⟨ 𝒯, 𝒞, ℰ, s₀, g ⟩')

    doc.add_paragraph('其中各元素定义如下：')

    defs=[
        ('𝒯 = {τ₁, τ₂, …, τₙ}',
         '子任务集合。每个子任务 τᵢ 为一个四元组 τᵢ = (nameᵢ, durᵢ, startᵢ, endᵢ)，'
         '其中 nameᵢ 为任务标识，durᵢ 为固定持续时间（秒），startᵢ 和 endᵢ 为待求解的起止时间变量，'
         '且满足 endᵢ = startᵢ + durᵢ。'),
        ('𝒞 = 𝒞_seq ∪ 𝒞_comm ∪ 𝒞_occ',
         '约束集合，包含顺序约束、通信窗口约束和遮挡约束三类（详见X.3节）。'),
        ('ℰ = {L_comm, L_occ}',
         '环境时间线集合，分别表示通信窗口状态和遮挡状态随时间的变化。'),
        ('s₀',
         '初始状态，包括机械臂初始位置和各环境时间线的初始状态。'),
        ('g',
         '目标状态，即所有子任务执行完毕（最后一个子任务的完成）。'),
    ]
    for sym,desc in defs:
        p=doc.add_paragraph()
        bold_run(p, f'{sym}：')
        p.add_run(desc)

    doc.add_paragraph(
        '规划问题的求解目标为：为每个子任务 τᵢ 确定 startᵢ 的取值，'
        '使得所有约束 𝒞 同时满足，且最后一个子任务在规划范围 [0, H] 内完成。'
    )

    doc.add_heading('X.2.2 持续时间模型',level=3)

    doc.add_paragraph(
        '对于涉及机械臂物理运动的子任务，其持续时间由梯形速度曲线（Trapezoidal Velocity Profile）决定。'
        '给定关节最大角速度 ω_max 和最大角加速度 α_max，对于角位移为 θ 的运动段，持续时间的解析表达式为：'
    )

    formula(doc, 'T(θ) = 2 · (ω_max / α_max) + (θ − ω²_max / α_max) / ω_max')

    doc.add_paragraph(
        '该公式包含加速段时间 t_acc = ω_max / α_max、匀速段时间 t_cruise = (θ − ω²_max / α_max) / ω_max '
        '和减速段时间 t_dec = t_acc 三个部分。上式成立的前提条件为 θ > ω²_max / α_max，'
        '即运动距离足够大以达到最大速度。对于非运动类子任务（如加电、设置参数等），持续时间由操作规程直接给定。'
    )

    doc.add_paragraph(
        '通过上述解析公式的预计算，将原本涉及连续动力学仿真的运动规划问题转化为固定时长的离散调度问题，'
        '这一步骤构成了时空解耦策略的核心：空间维度的运动学计算在规划前完成，'
        '规划过程仅处理时间维度的约束满足。'
    )

    # ────────────────────────────────────────
    doc.add_heading('X.3 约束建模',level=2)

    doc.add_heading('X.3.1 顺序约束',level=3)

    doc.add_paragraph(
        '子任务间的执行顺序关系构成一条有向因果链。'
        '定义顺序约束集合 𝒞_seq 如下：'
    )

    formula(doc, '𝒞_seq = { (τᵢ, τⱼ) | τᵢ meets τⱼ }，即 endᵢ = startⱼ')

    doc.add_paragraph(
        '其中 "meets" 表示 Allen 时序关系中的紧邻关系，'
        '即前一子任务的结束时刻恰好等于后一子任务的开始时刻，两者之间无间隔。'
        '在本模型中，同一阶段内的子任务均满足 meets 关系，形成严格的顺序链。'
    )

    doc.add_paragraph(
        '对于阶段间的衔接，考虑到通信窗口可能中断，允许相邻阶段之间存在等待间隔。'
        '定义弱顺序约束：'
    )

    formula(doc, '𝒞_weak = { (τᵢ, τⱼ) | τᵢ before τⱼ }，即 endᵢ ≤ startⱼ')

    doc.add_paragraph(
        '其中 "before" 表示前一子任务先于后一子任务完成，但允许中间存在空闲等待。'
    )

    doc.add_heading('X.3.2 通信窗口约束',level=3)

    doc.add_paragraph(
        '通信窗口时间线 L_comm 定义为一组不重叠的时间区间序列：'
    )

    formula(doc, 'L_comm = { [a₁,b₁], [a₂,b₂], …, [aₘ,bₘ] }，其中 bₖ ≤ aₖ₊₁')

    doc.add_paragraph(
        '区间 [aₖ, bₖ] 表示第 k 个通信可见窗口，窗口之间的间隔 [bₖ, aₖ₊₁] 表示通信中断期。'
        '通信窗口约束要求每个子任务的执行时段完全包含在某个通信可见窗口内：'
    )

    formula(doc, '∀τᵢ ∈ 𝒯, ∃k ∈ {1,…,m} : aₖ ≤ startᵢ ∧ endᵢ ≤ bₖ')

    doc.add_paragraph(
        '该约束在EUROPA中通过 contained_by 时序关系实现：子任务Token的时间区间'
        '必须被某个 InComms Token的时间区间所包含。'
    )

    doc.add_heading('X.3.3 遮挡约束',level=3)

    doc.add_paragraph(
        '遮挡状态时间线 L_occ 描述机械臂臂杆对通信链路的遮挡情况。'
        '遮挡计算依赖于三个要素的空间几何关系：空间站天线位置、中继卫星位置、机械臂各关节位置。'
    )

    doc.add_paragraph('遮挡判据定义为：')

    formula(doc, 'occlusion(t) = ∃ k ∈ {1,…,6} : dist(Segₖ(t), Link(t)) ≤ r₁ + r₂')

    doc.add_paragraph(
        '其中 Segₖ(t) 为第 k 段臂杆在时刻 t 的空间线段，Link(t) 为天线到中继卫星的通信链路线段，'
        'dist(·,·) 为两线段间的最短距离，r₁ 为臂杆等效半径，r₂ 为安全裕度。'
    )

    doc.add_paragraph(
        '臂杆空间位置通过以下坐标变换链计算：'
    )

    formula(doc, 'P_ECI = T_AB(t) · T_CB · FK(q)')

    doc.add_paragraph(
        '其中 FK(q) 为基于改进DH参数的正运动学函数，输入为七自由度关节角向量 q，'
        '输出各关节在臂基坐标系下的位置；T_CB 为臂基到空间站本体系的固定变换矩阵；'
        'T_AB(t) 为由SGP4轨道传播计算的空间站本体系到地心惯性系的时变变换矩阵。'
    )

    doc.add_paragraph(
        '遮挡状态时间线离散化为不重叠区间序列：'
    )

    formula(doc, 'L_occ = { (I₁, σ₁), (I₂, σ₂), … }，σₖ ∈ {Active, Inactive}')

    doc.add_paragraph(
        '对于在SWA工位附近执行的子任务集合 𝒯_swa ⊂ 𝒯（Phase 4和Phase 5的子任务），'
        '附加遮挡约束：'
    )

    formula(doc, '∀τᵢ ∈ 𝒯_swa, ∃ Iₖ : σₖ = Inactive ∧ startᵢ ≥ Iₖ.start ∧ endᵢ ≤ Iₖ.end')

    doc.add_paragraph(
        '该约束确保SWA附近的操作仅在遮挡不活跃的时间区间内执行。'
    )

    doc.add_heading('X.3.4 约束汇总',level=3)

    p=doc.add_paragraph()
    bold_run(p,'表X-1 约束类型汇总')
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER

    htable(doc,
        ['约束类型','数学表达','适用范围','EUROPA实现'],
        [
            ['持续时间','endᵢ = startᵢ + durᵢ','所有子任务','eq(duration, T)'],
            ['紧邻顺序','endᵢ = startⱼ','阶段内连续子任务','met_by(condition predecessor)'],
            ['通信窗口','∃k: aₖ ≤ startᵢ ∧ endᵢ ≤ bₖ','所有子任务','contained_by(InComms)'],
            ['遮挡回避','∃k: σₖ=Inactive ∧ Iₖ⊇[sᵢ,eᵢ]','SWA附近子任务','contained_by(Inactive)'],
            ['规划范围','0 ≤ startᵢ, endᵢ ≤ H','所有子任务','PlannerConfig(0, H)'],
        ]
    )
    doc.add_paragraph()

    # ────────────────────────────────────────
    doc.add_heading('X.4 时间线建模',level=2)

    doc.add_paragraph(
        'EUROPA框架采用时间线（Timeline）作为核心建模元素。'
        '时间线是一种特殊的对象，其上的Token（令牌）形成有序、不重叠的序列，'
        '自然地表达了"同一资源在同一时刻只能处于一种状态"的语义。'
        '本模型定义三条时间线：'
    )

    doc.add_heading('X.4.1 机械臂任务时间线',level=3)

    doc.add_paragraph(
        '机械臂任务时间线 Arm 承载所有子任务Token。'
        '每个子任务建模为Timeline上的action，求解器负责确定其在时间线上的位置。'
        '同一阶段的子任务通过 met_by 链式约束形成严格顺序。'
    )

    p=doc.add_paragraph()
    bold_run(p,'表X-2 机械臂任务时间线Token定义')
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER

    htable(doc,
        ['阶段','Token类型','持续时间(s)','前驱约束','附加约束'],
        [
            ['Phase 1a','BigArmRestart (fact)','980','— (T=0固定)','contained_by InComms'],
            ['Phase 1b','SmallArmRestart (fact)','150','— (T=25200固定)','contained_by InComms'],
            ['等待','WaitForMotion (fact)','可变','SmallArmRestart后','—'],
            ['Phase 2','Phase2 (action)','3530','met_by WaitForMotion','contained_by InComms'],
            ['Phase 3','Phase3 (action)','1840','met_by Phase2','contained_by InComms'],
            ['Phase 4','Phase4 (action)','770','met_by Phase3','InComms + OccInactive'],
            ['Phase 5','Phase5 (action)','460','met_by Phase4','InComms + OccInactive'],
            ['Phase 6','Phase6 (action)','1560','met_by Phase5','contained_by InComms'],
        ]
    )
    doc.add_paragraph()

    doc.add_paragraph(
        '其中Phase 1子任务作为fact（事实）直接放置在时间线的固定位置，'
        '体现了"大臂提前12小时、小臂提前5小时"的操作规程要求。'
        'Phase 2至Phase 6作为action（动作），由求解器在满足所有约束的前提下自动确定执行时间。'
    )

    doc.add_heading('X.4.2 通信窗口时间线',level=3)

    doc.add_paragraph(
        '通信窗口时间线 CommWindow 由交替排列的 InComms（通信可用）和 OutComms（通信中断）Token构成。'
        '每个Token的起止时间由轨道动力学预先计算确定，作为fact输入模型。'
        '该时间线仅包含两种谓词状态，形成完整的时间覆盖（无间隙、无重叠）。'
    )

    doc.add_paragraph(
        '通信窗口的计算基于SGP4轨道传播模型。给定空间站和中继卫星的TLE轨道根数，'
        '以固定时间步长传播两者的地心惯性坐标系（ECI）位置向量，'
        '逐时间步检测视线是否穿越地球球体：'
    )

    formula(doc, 'LOS_blocked(t) ⟺ ∃ λ∈(0,1) : ‖r_sta(t) + λ·(r_rel(t) − r_sta(t))‖ < R_E')

    doc.add_paragraph(
        '其中 r_sta(t) 和 r_rel(t) 分别为空间站和中继卫星在时刻 t 的ECI位置向量，R_E 为地球半径。'
        '将连续的可见/不可见状态聚合为离散区间序列，即得通信窗口时间线。'
    )

    doc.add_heading('X.4.3 遮挡状态时间线',level=3)

    doc.add_paragraph(
        '遮挡状态时间线 OcclusionSWA 由交替排列的 Active（遮挡活跃）和 Inactive（遮挡不活跃）Token构成。'
        '遮挡区间的计算流程如下：'
    )

    steps=[
        '基于改进DH参数表计算七自由度机械臂的正运动学，获得各关节在臂基坐标系下的位置。',
        '通过臂基到空间站本体系的固定变换矩阵 T_CB 和SGP4计算的时变变换矩阵 T_AB(t)，'
        '将关节位置转换到地心惯性坐标系。',
        '同步计算天线在ECI下的位置：P_ant(t) = T_AB(t) · T_tx_B · [0,0,0,1]ᵀ。',
        '对每个时间步，计算6段臂杆线段与天线-卫星通信链路线段之间的最短距离，'
        '判断是否小于阈值 r₁+r₂。',
        '将逐时间步的遮挡判定结果聚合为区间序列，输入遮挡状态时间线。',
    ]
    for i,s in enumerate(steps):
        doc.add_paragraph(f'({i+1}) {s}')

    # ────────────────────────────────────────
    doc.add_heading('X.5 NDDL建模编码',level=2)

    doc.add_paragraph(
        '基于上述形式化模型，使用EUROPA框架的NDDL（New Domain Definition Language）语言进行编码实现。'
        'NDDL是一种声明式建模语言，以类继承和谓词定义为基础，支持时间线、动作规则和约束的自然表达。'
    )

    doc.add_heading('X.5.1 时间线类定义',level=3)

    doc.add_paragraph(
        '模型定义三个Timeline子类，分别对应X.4节的三条时间线：'
    )

    code(doc, """
class CommWindow extends Timeline {
    predicate InComms  {}     // 通信可用状态
    predicate OutComms {}     // 通信中断状态
}

class OcclusionSWA extends Timeline {
    predicate Active   {}     // 遮挡活跃状态
    predicate Inactive {}     // 遮挡不活跃状态
}

class Arm extends Timeline {
    CommWindow   comm;        // 关联通信窗口时间线
    OcclusionSWA occlusion;   // 关联遮挡状态时间线

    action Phase2 {}          // 平台状态设置 (3530s)
    action Phase3 {}          // 大臂运动至组合 (1840s)
    action Phase4 {}          // 小臂运动至SWA  (770s)
    action Phase5 {}          // 视觉捕获SWA    (460s)
    action Phase6 {}          // 小臂独立设置   (1560s)
    predicate Done {}         // 任务完成标志
}""")
    doc.add_paragraph()

    doc.add_heading('X.5.2 动作规则编码',level=3)

    doc.add_paragraph(
        '每个action的规则体定义了持续时间约束、前驱因果约束和环境约束。'
        '以下以Phase 4（小臂运动至SWA）为例说明规则编码方式：'
    )

    code(doc, """
Arm::Phase4 {
    eq(duration, 770);        // 持续时间约束: dur = 770s
    met_by(condition object.Phase3);
                              // 顺序约束: Phase3 紧邻先于 Phase4
    contained_by(condition object.comm.InComms);
                              // 通信约束: 完全包含于某个InComms窗口
    contained_by(condition object.occlusion.Inactive);
                              // 遮挡约束: 完全包含于某个Inactive区间
}""")
    doc.add_paragraph()

    doc.add_paragraph(
        '当求解器激活Phase4 Token时，规则引擎自动执行以下操作：'
    )

    rule_effects=[
        'eq(duration, 770) → 在STN中添加约束边 start→end(770) 和 end→start(−770)。',
        'met_by(Phase3) → 创建Phase3子Token（若不存在则为新的OpenCondition缺陷），添加约束 Phase3.end = Phase4.start。',
        'contained_by(InComms) → 创建InComms子Token（需与已有窗口fact合并），添加约束 InComms.start ≤ Phase4.start ∧ Phase4.end ≤ InComms.end。',
        'contained_by(Inactive) → 创建Inactive子Token，添加约束 Inactive.start ≤ Phase4.start ∧ Phase4.end ≤ Inactive.end。',
    ]
    for i,r in enumerate(rule_effects):
        doc.add_paragraph(f'({i+1}) {r}')

    doc.add_heading('X.5.3 问题实例编码',level=3)

    doc.add_paragraph(
        '问题实例文件定义对象创建、环境时间线的fact序列和规划目标：'
    )

    code(doc, """
// 创建对象并关联时间线
CommWindow   commState = new CommWindow();
OcclusionSWA occSWA    = new OcclusionSWA();
Arm          arm       = new Arm(commState, occSWA);
close();

// 通信窗口 fact 序列 (由轨道计算预先确定)
fact(commState.InComms c1);  eq(c1.start,0);     eq(c1.end,4000);
fact(commState.OutComms g1); eq(g1.start,4000);   eq(g1.end,22000);
...

// 遮挡状态 fact 序列 (由运动学+轨道联合计算确定)
fact(occSWA.Inactive o1);    eq(o1.start,0);      eq(o1.end,40000);
fact(occSWA.Active o2);      eq(o2.start,40000);   eq(o2.end,40400);
...

// Phase 1 子任务 (固定时间放置)
fact(arm.BigArmRestart p1a);
eq(p1a.start, 0); eq(p1a.duration, 980);

// 规划目标
goal(arm.Done missionGoal);""")
    doc.add_paragraph()

    # ────────────────────────────────────────
    doc.add_heading('X.6 模型验证与分析',level=2)

    doc.add_heading('X.6.1 模型规模',level=3)

    p=doc.add_paragraph()
    bold_run(p,'表X-3 模型规模参数')
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER

    htable(doc,
        ['参数','数值','说明'],
        [
            ['子任务总数','23','6个阶段共23个子任务'],
            ['action Token数','5','Phase 2-6（阶段级聚合）'],
            ['fact Token数','10+','Phase 1 + WaitForMotion + 通信/遮挡序列'],
            ['通信窗口数','7','4个InComms + 3个OutComms'],
            ['遮挡区间数','3','1个Active + 2个Inactive'],
            ['STN时间点数','~80','每个Token贡献start, end, duration三个时间点'],
            ['STN约束边数','~160','每个约束贡献2条边（上界+下界）'],
            ['规划范围','55000秒','约15.3小时'],
        ]
    )
    doc.add_paragraph()

    doc.add_heading('X.6.2 建模策略讨论',level=3)

    doc.add_paragraph(
        '在建模过程中采用了以下关键设计策略：'
    )

    strategies=[
        ('阶段级聚合',
         '将同一阶段内严格顺序的多个子任务聚合为单一action Token，'
         '持续时间取子任务时长之和。该策略将21个action Token缩减为5个，'
         '显著降低了求解器的搜索空间。聚合的合理性在于同一阶段的子任务无独立调度自由度——'
         '其内部顺序固定，且共享相同的通信窗口约束。'),
        ('Fact与Action分离',
         'Phase 1的重启加电子任务作为fact固定放置（不由求解器调度），'
         '仅Phase 2-6的主操作链作为action由求解器决策。'
         '该策略反映了实际操作规程中"提前量"的刚性约束，同时减少了求解器的决策变量。'),
        ('通信窗口宽度设计',
         '通信窗口的宽度必须大于最长阶段的持续时间（Phase 2为3530秒），'
         '否则该阶段的 contained_by 约束将无法满足。'
         '在实际应用中，需根据中继卫星轨道和地面站分布计算真实窗口，'
         '并验证其能否容纳各阶段的操作时长。'),
        ('遮挡约束的选择性施加',
         '仅对SWA工位附近的操作（Phase 4和Phase 5）施加遮挡约束，'
         '其他阶段的操作位置远离天线视线方向，无遮挡风险。'
         '这一选择性建模避免了不必要的约束，提高了求解效率。'),
    ]
    for i,(title_t,desc) in enumerate(strategies):
        p=doc.add_paragraph()
        bold_run(p,f'({i+1}) {title_t}。')
        p.add_run(desc)

    # ────────────────────────────────────────
    doc.add_heading('X.7 本章小结',level=2)

    doc.add_paragraph(
        '本章对空间站机械臂在轨作业任务规划问题进行了系统的形式化建模。'
        '首先，将规划问题定义为包含子任务集合、约束集合和环境时间线的约束满足问题；'
        '其次，从数学角度严格定义了顺序约束、通信窗口约束和遮挡约束三类约束；'
        '再次，基于EUROPA的时间线建模范式，设计了机械臂任务、通信窗口和遮挡状态三条时间线，'
        '并给出了遮挡计算的坐标变换链和判据公式；'
        '最后，使用NDDL语言完成了模型的编码实现，并讨论了阶段级聚合、Fact-Action分离等关键建模策略。'
        '该模型为后续章节的算法求解和实验分析奠定了基础。'
    )

    # Save
    p1='/opt/cursor/artifacts/modeling_chapter.docx'
    p2='/workspace/documentation/modeling_chapter.docx'
    doc.save(p1); doc.save(p2)
    print(f"Saved: {p1}\nSaved: {p2}")

if __name__=='__main__':
    create()
