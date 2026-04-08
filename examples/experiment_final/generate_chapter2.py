#!/usr/bin/env python3
"""
Generate complete Chapter 2: Robotic Arm Task Planning Modeling and Solving.
Incorporates all reviewer suggestions for logical flow and academic rigor.
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn

OUT = '/workspace/examples/experiment_final'

def shd(c, cl):
    pr = c._element.get_or_add_tcPr()
    pr.append(pr.makeelement(qn('w:shd'),{qn('w:val'):'clear',qn('w:color'):'auto',qn('w:fill'):cl}))

def htb(doc, hd, rows):
    t = doc.add_table(rows=1+len(rows), cols=len(hd), style='Table Grid')
    for i, h in enumerate(hd):
        c = t.rows[0].cells[i]; c.text = h; c.paragraphs[0].runs[0].bold = True; shd(c, 'D9E2F3')
    for ri, row in enumerate(rows):
        for ci, v in enumerate(row): t.rows[ri+1].cells[ci].text = str(v)

def code(doc, text):
    for ln in text.strip().split('\n'):
        p = doc.add_paragraph(); p.style = doc.styles['code']; p.add_run(ln)

def fm(doc, text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text); r.italic = True; return p

def br(p, text):
    r = p.add_run(text); r.bold = True; return r

def create():
    doc = Document()
    s = doc.styles['Normal']; s.font.name = 'Times New Roman'; s.font.size = Pt(12)
    s.paragraph_format.line_spacing = 1.5; s.paragraph_format.space_after = Pt(6)
    rPr = s.element.get_or_add_rPr()
    rPr.append(rPr.makeelement(qn('w:rFonts'), {qn('w:eastAsia'): '宋体'}))
    for lv in range(1, 4):
        h = doc.styles[f'Heading {lv}']; h.font.color.rgb = RGBColor(0,0,0)
        h.font.bold = True; h.font.size = Pt([0, 16, 14, 12][lv])
    cs = doc.styles.add_style('code', WD_STYLE_TYPE.PARAGRAPH)
    cs.font.name = 'Consolas'; cs.font.size = Pt(9)
    cs.paragraph_format.space_before = Pt(0); cs.paragraph_format.space_after = Pt(0)
    cs.paragraph_format.line_spacing = 1.15; cs.paragraph_format.left_indent = Cm(1)

    # ════════════════════════════════════════
    title = doc.add_heading('第2章 空间站机械臂作业任务规划建模与求解', level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(
        '空间站机械臂在轨作业任务规划问题涉及离散的任务状态转换与连续的时序约束推理，'
        '是一类典型的混合约束满足问题。本章首先建立问题的总体描述（2.1节），'
        '然后给出时间线规划系统的形式化定义（2.2节），在此基础上对约束体系进行系统建模（2.3节），'
        '利用NDDL语言完成编码实现（2.4节），设计动作规则体系（2.5节），'
        '最后给出基于缺陷导向搜索与简单时序网络传播的求解算法（2.6节）。')

    # ════════════════════════════════════════
    # 2.1
    # ════════════════════════════════════════
    doc.add_heading('2.1 问题概述', level=2)

    doc.add_paragraph(
        '空间站机械臂在轨作业任务规划问题可抽象为一类带时序约束和资源约束的调度问题。'
        '机械臂需执行一系列预定义的操作子任务，每个子任务具有固定的持续时间和严格的执行顺序。'
        '任务执行过程受到两类环境约束的限制：其一，所有操作必须在中继卫星提供的通信可见窗口内完成；'
        '其二，当机械臂在SWA（转位机构）附近作业时，臂杆可能遮挡空间站天线与中继卫星之间的通信链路，'
        '须回避遮挡区间。')

    doc.add_paragraph(
        '上述问题的核心挑战在于：（1）通信窗口的周期性中断（每轨道圈约42分钟不可用）限制了任务的连续执行；'
        '（2）遮挡约束与通信约束的空间耦合——遮挡仅在通信可用期间有实际影响；'
        '（3）提前量约束（大臂重启需在运动前12小时、小臂重启需在运动前5小时完成）'
        '跨越多个轨道圈次，增加了调度的时间跨度；'
        '（4）部分阶段（如Phase 2平台设置，总时长3530秒）超过单个通信窗口容量（约3400秒），'
        '需自动拆分到相邻窗口执行。'
        '规划算法需在满足上述所有约束的前提下确定各子任务的可行执行时间。')

    # ════════════════════════════════════════
    # 2.2
    # ════════════════════════════════════════
    doc.add_heading('2.2 时间线规划系统形式化定义', level=2)

    doc.add_paragraph(
        '本节采用EUROPA框架的时间线规划范式对问题进行形式化建模。'
        '时间线规划范式的核心思想是：将系统中每个资源或对象建模为一条时间线，'
        '时间线上的Token（令牌）表示该资源在某时段内的状态或动作，'
        'Token形成有序不重叠序列，自然表达了"同一资源在同一时刻只能处于一种状态"的语义。')

    # Definition 1
    doc.add_heading('2.2.1 时间线规划系统', level=3)

    p = doc.add_paragraph(); br(p, '定义1（时间线规划系统）')
    doc.add_paragraph('时间线规划系统（Timeline Planning System, TPS）𝒮 是一个五元组：')
    fm(doc, '𝒮 = (𝒪, ℒ, 𝒯, 𝒞, ℛ)                (1)')
    doc.add_paragraph('式中，各元素定义如下：')

    defs = [
        ('𝒪 = {o₁, o₂, …, oₘ}',
         '为有限对象集合。每个对象 oᵢ 通过双射 L: 𝒪 → ℒ 关联一条时间线 L(oᵢ) = Lᵢ。'),
        ('ℒ = {L₁, L₂, …, Lₘ}',
         '为时间线集合。每条时间线 Lᵢ 上的Token形成有序不重叠序列，'
         '即对于同一时间线上任意相邻Token τⱼ 和 τⱼ₊₁，有 end(τⱼ) ≤ start(τⱼ₊₁)。'),
        ('𝒯',
         '为Token类型集合，分为谓词（predicate）和动作（action）两类。'
         '每个Token τ 具有类型 type(τ)、起始时间 start(τ)、结束时间 end(τ) 和持续时间 dur(τ) = end(τ) − start(τ)。'),
        ('𝒞',
         '为约束集合，包含时序约束（定义在Token时间变量上的线性不等式）和参数约束'
         '（定义在Token参数变量上的等式或不等式），详见2.3节。'),
        ('ℛ',
         '为规则集合。每条规则 r ∈ ℛ 关联一个Token类型，定义该类型Token被激活时'
         '自动创建的子Token和约束，详见2.5节。'),
    ]
    for sym, desc in defs:
        p = doc.add_paragraph(); br(p, f'{sym} '); p.add_run(desc)

    # Definition 2
    doc.add_heading('2.2.2 部分计划', level=3)

    p = doc.add_paragraph(); br(p, '定义2（部分计划）')
    doc.add_paragraph('部分计划（Partial Plan）PP 是一个三元组：')
    fm(doc, 'PP = (Tokens, Active, Constraints)                (2)')
    doc.add_paragraph('式中：')
    items = [
        'Tokens 为当前计划中所有Token的集合；',
        'Active ⊆ Tokens 为已激活（放置到时间线上）的Token子集；',
        'Constraints 为当前所有约束的集合，包含Token间的时序约束和参数约束。',
    ]
    for it in items: doc.add_paragraph(it, style='List Bullet')

    doc.add_paragraph(
        '给定部分计划PP，其缺陷集合 Flaws(PP) 由以下三类缺陷构成（定义3）。'
        '当 Flaws(PP) = ∅ 时，PP 为完整计划。')

    # Definition 3
    doc.add_heading('2.2.3 缺陷', level=3)

    p = doc.add_paragraph(); br(p, '定义3（缺陷）')
    doc.add_paragraph('部分计划PP中的缺陷分为三类：')

    doc.add_paragraph(
        '（1）开放条件（Open Condition）：Token τ ∈ Tokens \\ Active，'
        '即存在于计划中但尚未放置到任何时间线上的Token。')
    doc.add_paragraph(
        '（2）时序威胁（Threat）：已激活Token τ ∈ Active '
        '在其所属时间线上与其他Token的排序未确定。')
    doc.add_paragraph(
        '（3）未绑定变量（Unbound Variable）：已激活Token τ ∈ Active '
        '的某参数变量 v 的值域 |Dom(v)| > 1，尚未收窄为单值。')

    doc.add_paragraph(
        '三类缺陷的解决策略将在2.6节求解算法中详细描述。')

    # Definition 4
    doc.add_heading('2.2.4 简单时序网络', level=3)

    p = doc.add_paragraph(); br(p, '定义4（简单时序网络）')
    doc.add_paragraph('简单时序网络（Simple Temporal Network, STN）N 是一个三元组：')
    fm(doc, 'N = (V, E, O)                (3)')
    doc.add_paragraph('式中：')
    items4 = [
        'V = {v₁, v₂, …, vₙ} 为时间点集合，每个Token τ 贡献三个时间点 start(τ), end(τ), dur(τ)；',
        'E ⊆ V × V × ℝ 为有向加权边集合，边 (vᵢ, vⱼ, w) 表示约束 vⱼ − vᵢ ≤ w；',
        'O ∈ V 为参考原点，所有时间点的界相对于O定义。',
    ]
    for it in items4: doc.add_paragraph(it, style='List Bullet')

    doc.add_paragraph('时序约束 lb ≤ Tⱼ − Tᵢ ≤ ub 在STN中编码为两条有向边：')
    fm(doc, 'Tᵢ →^{ub} Tⱼ（上界边：Tⱼ − Tᵢ ≤ ub）\nTⱼ →^{−lb} Tᵢ（下界边：Tᵢ − Tⱼ ≤ −lb）                (4)')

    p = doc.add_paragraph(); br(p, '性质1')
    doc.add_paragraph(
        '时间点T的上下界由最短路径决定：'
        'upperBound(T) = δ(O, T)（O到T的最短路径 = 最晚可能时刻），'
        'lowerBound(T) = −δ(T, O)（T到O的最短路径的相反数 = 最早可能时刻）。'
        '约束系统一致当且仅当距离图中不存在负权环路。')

    # Definition 5
    doc.add_heading('2.2.5 机械臂作业规划问题', level=3)

    p = doc.add_paragraph(); br(p, '定义5（机械臂作业规划问题）')
    doc.add_paragraph('机械臂作业规划问题是TPS上的约束满足问题 𝒫：')
    fm(doc, '𝒫 = (𝒮, s₀, 𝒢, H)                (5)')
    doc.add_paragraph('式中：')
    items5 = [
        '𝒮 = (𝒪, ℒ, 𝒯, 𝒞, ℛ) 为时间线规划系统（定义1），对象集合 𝒪 = {Arm, CommWindow, OcclusionSWA}；',
        's₀ 为初始部分计划，包含环境时间线上的Fact Token（通信窗口序列、遮挡状态序列）和Phase 1子任务的固定放置；',
        '𝒢 为目标条件，即Token Done被激活且 start(Done) ≤ H；',
        'H 为规划范围上界。',
    ]
    for it in items5: doc.add_paragraph(it, style='List Bullet')

    doc.add_paragraph('问题的解是一个完整计划 PP*，满足以下三个条件：')
    doc.add_paragraph('（1）Flaws(PP*) = ∅（无缺陷）；')
    doc.add_paragraph('（2）对所有已激活Token τ ∈ Active(PP*)，lb(start(τ)) ≤ ub(start(τ))（时序一致）；')
    doc.add_paragraph(
        '（3）对所有操作Token τᵢ，存在通信窗口 [aₖ, bₖ] 使得 aₖ ≤ start(τᵢ) ∧ end(τᵢ) ≤ bₖ。')

    # ════════════════════════════════════════
    # 2.3
    # ════════════════════════════════════════
    doc.add_heading('2.3 约束建模', level=2)

    doc.add_paragraph('基于定义1中的约束集合𝒞，本节对机械臂作业规划中的四类约束进行系统建模。')

    # 2.3.1
    doc.add_heading('2.3.1 顺序约束', level=3)

    doc.add_paragraph(
        '子任务间的执行顺序关系构成因果链。同一阶段内相邻子任务满足紧邻约束（Allen关系中的meets）：')
    fm(doc, 'C_SEQ = { (τᵢ, τⱼ) | τᵢ meets τⱼ }，即 end(τᵢ) = start(τⱼ)                (6)')
    doc.add_paragraph(
        '阶段间的衔接考虑到通信窗口可能中断，允许相邻阶段之间存在等待间隔，满足弱顺序约束：')
    fm(doc, 'C_weak = { (τᵢ, τⱼ) | τᵢ before τⱼ }，即 end(τᵢ) ≤ start(τⱼ)                (7)')

    # 2.3.2
    doc.add_heading('2.3.2 通信窗口约束', level=3)

    doc.add_paragraph(
        '通信窗口时间线定义为一组不重叠的时间区间序列，由SGP4轨道传播模型计算空间站'
        '与中继卫星的相对可见性确定：')
    fm(doc, 'L_COMM = { [a₁,b₁], [a₂,b₂], …, [aₘ,bₘ] }，其中 bₖ ≤ aₖ₊₁                (8)')
    doc.add_paragraph(
        '通信窗口约束要求每个操作子任务的执行时段完全包含在某个通信可见窗口内：')
    fm(doc, '∀τᵢ ∈ 𝒯_op, ∃k ∈ {1,…,m}: aₖ ≤ start(τᵢ) ∧ end(τᵢ) ≤ bₖ                (9)')

    # 2.3.3
    doc.add_heading('2.3.3 遮挡约束', level=3)

    doc.add_paragraph(
        '遮挡状态时间线描述机械臂臂杆对通信链路的遮挡情况。遮挡状态通过SGP4轨道传播'
        '联合DH运动学正解计算确定（详见第X章），离散化为区间序列：')
    fm(doc, 'L_OCC = { (I₁,σ₁), (I₂,σ₂), … }，σₖ ∈ {Active, Inactive}                (10)')
    doc.add_paragraph(
        '对于SWA工位附近的操作子任务集合 𝒯_SWA ⊂ 𝒯（Phase 4和Phase 5），附加遮挡回避约束：')
    fm(doc, '∀τᵢ ∈ 𝒯_SWA, ∃Iₖ: σₖ = Inactive ∧ start(τᵢ) ≥ Iₖ.start ∧ end(τᵢ) ≤ Iₖ.end                (11)')
    doc.add_paragraph(
        '需要指出，遮挡仅在通信可用期间有实际影响。'
        '若遮挡区间落在通信中断期内（如算例中遮挡②[75450,76110]落在通信间隙[74580,76880]内），'
        '则该遮挡为无效遮挡，不影响任务规划。')

    # 2.3.4
    doc.add_heading('2.3.4 提前量约束', level=3)

    doc.add_paragraph('大臂和小臂的重启加电保温需满足操作规程要求的提前量：')
    fm(doc, 'end(τ_BA) + 43200 ≤ start(τ_P3)    （大臂重启在Phase 3前≥12小时完成）\n'
       'end(τ_SA) + 18000 ≤ start(τ_P4)    （小臂重启在Phase 4前≥5小时完成）                (12)')

    # 2.3.5
    doc.add_heading('2.3.5 约束汇总', level=3)

    p = doc.add_paragraph(); br(p, '表2-1 约束类型汇总')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    htb(doc, ['约束类型', '数学表达', '适用范围', 'NDDL实现'],
        [['持续时间', 'end(τ) = start(τ) + dur(τ)', '所有子任务', 'eq(duration, T)'],
         ['紧邻顺序', 'end(τᵢ) = start(τⱼ)', '阶段内连续子任务', 'met_by(condition pred)'],
         ['通信窗口', '∃k: aₖ≤start(τ) ∧ end(τ)≤bₖ', '所有操作子任务', 'contained_by(InComms)'],
         ['遮挡回避', '∃k: σₖ=Inactive ∧ Iₖ⊇[s,e]', 'SWA附近子任务', 'contained_by(Inactive)'],
         ['大臂提前', 'end(τ_BA)+43200≤start(τ_P3)', '大臂重启', '时间变量约束'],
         ['小臂提前', 'end(τ_SA)+18000≤start(τ_P4)', '小臂重启', '时间变量约束']])
    doc.add_paragraph()

    # ════════════════════════════════════════
    # 2.4
    # ════════════════════════════════════════
    doc.add_heading('2.4 NDDL建模编码', level=2)

    doc.add_paragraph(
        '基于上述形式化模型，使用EUROPA框架的NDDL（New Domain Definition Language）语言进行编码。'
        'NDDL是一种声明式建模语言，以类继承和谓词定义为基础，支持时间线、动作规则和约束的自然表达。')

    doc.add_heading('2.4.1 时间线类定义', level=3)

    doc.add_paragraph(
        '以下NDDL代码实现了定义1中TPS的三个对象 𝒪 = {Arm, CommWindow, OcclusionSWA} '
        '及其关联的时间线类型。时间线是一种特殊的对象，其上的Token形成有序不重叠序列，'
        '自然表达了定义1中时间线ℒ的语义。')

    code(doc, """
class CommWindow extends Timeline {
    predicate InComms  {}      // 通信可用状态
    predicate OutComms {}      // 通信中断状态
}

class OcclusionSWA extends Timeline {
    predicate Active   {}      // 遮挡活跃状态
    predicate Inactive {}      // 遮挡不活跃状态
}

class Arm extends Timeline {
    CommWindow   comm;         // 关联通信窗口时间线
    OcclusionSWA occlusion;   // 关联遮挡状态时间线

    action Phase2A {}          // 平台设置-帆板+相机 (2410s)
    action Phase2B {}          // 平台设置-禁止项 (1120s)
    action Phase3  {}          // 大臂运动至组合 (1840s)
    action Phase4  {}          // 小臂运动至SWA  (770s)
    action Phase5  {}          // 视觉捕获SWA    (460s)
    action Phase6  {}          // 小臂独立设置   (1560s)
    predicate Done {}          // 任务完成标志
}""")
    doc.add_paragraph()

    doc.add_paragraph(
        '其中Phase 2因总时长（3530秒）超过单个通信窗口容量（约3400秒），'
        '拆分为Phase2A（太阳帆板+舱外相机设置，2410秒）和Phase2B（禁止项设置，1120秒），'
        '分别在不同通信窗口内执行。')

    # ════════════════════════════════════════
    # 2.5
    # ════════════════════════════════════════
    doc.add_heading('2.5 动作规则编码', level=2)

    doc.add_paragraph(
        '每个action的规则体定义了该动作被激活时自动创建的子Token和约束，'
        '对应定义1中的规则集合ℛ。以Phase 4（小臂运动至SWA）为例说明规则编码方式，'
        '该阶段同时涉及持续时间约束（公式4）、顺序约束（公式6）、通信约束（公式9）'
        '和遮挡约束（公式11）四类约束，是约束最完整的典型动作：')

    code(doc, """
Arm::Phase4 {
    eq(duration, 770);
        // 持续时间约束: dur(τ) = 770s → 公式(4)
    met_by(condition object.Phase3);
        // 顺序约束: Phase3紧邻先于Phase4 → 公式(6)
    contained_by(condition object.comm.InComms);
        // 通信约束: 完全包含于某个InComms窗口 → 公式(9)
    contained_by(condition object.occlusion.Inactive);
        // 遮挡约束: 完全包含于某个Inactive区间 → 公式(11)
}""")
    doc.add_paragraph()

    doc.add_paragraph(
        '当求解器激活Phase4 Token时，规则引擎自动执行以下操作：'
        '（1）eq(duration, 770)在STN中添加约束边 start→end(770) 和 end→start(−770)；'
        '（2）met_by(Phase3)创建Phase3子Token（若不存在则为新的开放条件缺陷），'
        '添加约束 Phase3.end = Phase4.start；'
        '（3）contained_by(InComms)创建InComms子Token（需与已有窗口Fact合并），'
        '添加约束 InComms.start ≤ Phase4.start ∧ Phase4.end ≤ InComms.end；'
        '（4）contained_by(Inactive)创建Inactive子Token，添加类似的包含约束。')

    # ════════════════════════════════════════
    # 2.6
    # ════════════════════════════════════════
    doc.add_heading('2.6 求解算法', level=2)

    doc.add_paragraph(
        '基于2.2节建立的形式化模型和2.3节定义的约束体系，本节给出求解算法的完整流程。'
        '求解算法的核心是缺陷导向的时序回溯搜索（Flaw-Directed Temporal Backtracking Search），'
        '分为三个阶段：约束网络构建、缺陷导向搜索、计划提取。')

    # 2.6.1
    doc.add_heading('2.6.1 求解流程', level=3)

    doc.add_paragraph('图2-1给出了完整的求解流程。')

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(); r.add_picture(f'{OUT}/europa_flowchart.png', width=Inches(4.5))
    p2 = doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.add_run('图2-1 EUROPA求解机械臂任务规划流程').italic = True
    doc.add_paragraph()

    doc.add_paragraph(
        '如图2-1所示，Phase 1通过ANTLR3解析器读入NDDL模型，创建三条Timeline上的初始Token。'
        'Phase 2为所有Token的时间变量构建STN约束网络（定义4），通过Bellman-Ford算法计算势函数。'
        'Phase 3至Phase 6构成核心搜索循环：传播—选缺陷—决策—规则触发—验证—回溯。'
        'Phase 7验证提前量约束（公式12），Phase 8提取可执行计划。')

    # 2.6.2
    doc.add_heading('2.6.2 约束网络构建', level=3)

    p = doc.add_paragraph(); br(p, '算法1 BUILD_STN过程')
    code(doc, """
输入: NDDL域模型 M, 问题实例 P
输出: 初始STN N, 初始部分计划 PP₀

过程 BUILD_STN(M, P):
  Schema ← PARSE_NDDL(M)
  PP₀ ← INSTANTIATE(P, Schema)
  N ← (V=∅, E=∅, O=origin)
  FOR EACH τ ∈ PP₀.Tokens:
    ADD_TIMEPOINT(N, start(τ)); ADD_TIMEPOINT(N, end(τ))
    ADD_EDGE(N, start(τ), end(τ), dur(τ))       // 公式(4)上界边
    ADD_EDGE(N, end(τ), start(τ), -dur(τ))      // 公式(4)下界边
  FOR EACH τ ∈ PP₀.Facts:
    ADD_EDGE(N, O, start(τ), start_val(τ))
    ADD_EDGE(N, start(τ), O, -start_val(τ))
  consistent ← BELLMAN_FORD(N)
  IF ¬consistent: RETURN FAIL
  RETURN (N, PP₀)""")
    doc.add_paragraph()

    # 2.6.3
    doc.add_heading('2.6.3 缺陷导向搜索主循环', level=3)

    p = doc.add_paragraph(); br(p, '算法2 Solve过程')
    code(doc, """
输入: STN N, 部分计划 PP₀, 最大步数 N_max
输出: 完整计划 PP* 或 FAIL

过程 Solve(N, PP₀, N_max):
  Stack ← ∅;  PP ← PP₀;  n ← 0
  WHILE n < N_max:
    consistent ← INC_PROPAGATE(N)             // 步骤1: 约束传播
    IF ¬consistent ∧ Stack=∅: RETURN FAIL
    flaw ← SELECT_FLAW(PP)                    // 步骤2: 缺陷选择
    IF flaw = ∅: RETURN PP                    // 无缺陷→成功
    dp ← CREATE_DECISION(flaw)                // 步骤3: 决策生成
    dp.EXECUTE();  n ← n+1                    // 执行决策
    IF dp.type = ACTIVATE:                    // 步骤3.5: 规则触发
      FOR EACH rule ∈ ℛ(type(dp.token)):
        FIRE_RULE(rule, PP, N)
    consistent ← INC_PROPAGATE(N)             // 步骤4: 验证
    IF consistent:
      Stack.PUSH(dp)                          // 成功,入栈
    ELSE:
      exhausted ← BACKTRACK(dp, Stack, PP, N) // 步骤5: 回溯
      IF exhausted: RETURN FAIL
  RETURN TIMEOUT""")
    doc.add_paragraph()

    doc.add_paragraph(
        '缺陷选择（步骤2）的核心策略：①零承诺优先——优先处理仅有唯一解决方案的缺陷'
        '（如规则触发创建的effect Token只能合并到特定Fact），不引入搜索分支；'
        '②优先级排序——按管理器优先级（ThreatManager → OpenConditionManager → UnboundVariableManager）选择。')

    doc.add_paragraph(
        '决策执行（步骤3）根据缺陷类型（定义3）选择操作：'
        '对开放条件执行ACTIVATE/MERGE/REJECT；对时序威胁执行ORDER；对未绑定变量执行SPECIFY。'
        '其中ACTIVATE触发规则引擎（步骤3.5），自动创建子Token和约束，驱动反向链式推理。')

    # 2.6.4
    doc.add_heading('2.6.4 缺陷选择', level=3)

    p = doc.add_paragraph(); br(p, '算法3 Allocate_Decision过程')
    code(doc, """
输入: 缺陷管理器集合 FM
输出: 决策点 dp 或 ∅

过程 Allocate_Decision(FM):
  // 零承诺优先
  FOR EACH fm ∈ FM:
    d ← fm.NEXT_ZERO_COMMITMENT()
    IF d ≠ ∅: d.INITIALIZE(); RETURN d
  // 优先级排序
  best ← ∅;  bestP ← +∞
  FOR EACH fm ∈ FM:
    FOR EACH flaw ∈ fm.CANDIDATES():
      IF fm.FILTERED(flaw): CONTINUE
      p ← fm.PRIORITY(flaw)
      IF p < bestP: best ← fm.CREATE_DECISION(flaw); bestP ← p
  IF best ≠ ∅: best.INITIALIZE()
  RETURN best""")
    doc.add_paragraph()

    # 2.6.5
    doc.add_heading('2.6.5 时序回溯', level=3)

    p = doc.add_paragraph(); br(p, '算法4 Backtrack过程')
    code(doc, """
过程 Backtrack(dp, Stack, PP, N):
  WHILE dp ≠ ∅ ∨ Stack ≠ ∅:
    IF dp = ∅: dp ← Stack.POP()
    IF dp.IS_EXECUTED(): dp.UNDO(PP, N)
    IF dp.HAS_NEXT_CHOICE(): RETURN false    // 找到替代分支
    ELSE: DELETE dp; dp ← ∅                  // 继续回溯
  RETURN true                                // 搜索空间耗尽""")
    doc.add_paragraph()

    doc.add_paragraph(
        '回溯的关键特性在于UNDO操作的可逆性：当决策被撤销时，该决策添加到STN中的约束边被移除。'
        '由于约束删除可能使之前被排除的路径重新可行，STN需执行完全重传播'
        '（Bellman-Ford + 双向Dijkstra），这是回溯代价的主要来源。')

    # 2.6.6
    doc.add_heading('2.6.6 STN增量传播', level=3)

    doc.add_paragraph(
        'STN增量传播是保证求解效率的关键。由于下界边权重为负值（公式4），'
        '标准Dijkstra不可直接使用。本算法采用Johnson重标号技术：')
    fm(doc, "w'(u, v) = w(u, v) + π(u) − π(v) ≥ 0                (13)")

    p = doc.add_paragraph(); br(p, '算法5 INC_PROPAGATE过程')
    code(doc, """
过程 INC_PROPAGATE(N, src, targ):
  // 阶段1: 一致性检查(增量Bellman-Ford)
  IF RELAXABLE(src, targ): IF ¬INC_BELLMAN_FORD(N): RETURN false
  // 阶段2: 上界传播(前向Dijkstra, 算法6)
  IF src.ub + edge.w < targ.ub:
    targ.ub ← src.ub + edge.w; Queue.INSERT(targ)
    DIJKSTRA_FORWARD(N, Queue)
  // 阶段3: 下界传播(后向Dijkstra, 算法7)
  IF (-targ.lb) + edge.w < (-src.lb):
    src.lb ← -((-targ.lb) + edge.w); Queue.INSERT(src)
    DIJKSTRA_BACKWARD(N, Queue)
  RETURN true""")
    doc.add_paragraph()

    p = doc.add_paragraph(); br(p, '算法6 Dijkstra_Forward（上界传播）')
    code(doc, """
WHILE Queue ≠ ∅:
  node ← Queue.POP_MIN()
  FOR EACH edge ∈ node.outEdges:
    next ← edge.to
    newDist ← node.upperBound + edge.weight
    IF newDist < next.upperBound:
      next.upperBound ← newDist
      next.depth ← node.depth + 1
      IF next.depth > |V|: MARK_INCONSISTENT(); RETURN  // 负环
      key ← newDist - next.π     // Johnson重标号
      Queue.INSERT(next, key)""")
    doc.add_paragraph()

    p = doc.add_paragraph(); br(p, '算法7 Dijkstra_Backward（下界传播）')
    code(doc, """
WHILE Queue ≠ ∅:
  node ← Queue.POP_MIN()
  FOR EACH edge ∈ node.inEdges:    // 遍历入边
    next ← edge.from               // 反向传播
    newDist ← (-node.lowerBound) + edge.weight
    IF newDist < (-next.lowerBound):
      next.lowerBound ← -newDist
      next.depth ← node.depth + 1
      IF next.depth > |V|: MARK_INCONSISTENT(); RETURN
      key ← newDist + next.π
      Queue.INSERT(next, key)""")
    doc.add_paragraph()

    doc.add_paragraph(
        '增量传播的核心优化在于START_NODE函数执行的可行性预检：'
        '若新约束不能改进任一端点的距离值，传播在O(1)内终止。'
        '对于本算例（V≈80, E≈160），每次增量传播在微秒量级完成。')

    # 2.6.7
    doc.add_heading('2.6.7 计划提取', level=3)

    p = doc.add_paragraph(); br(p, '算法8 EXTRACT_PLAN过程')
    code(doc, """
过程 EXTRACT_PLAN(PP*, N):
  Plan ← ∅
  FOR EACH τ ∈ PP*.Active (按时间线顺序):
    s ← lb(start(τ));  e ← s + dur(τ)
    Plan.ADD( (type(τ), s, e, dur(τ)) )
    ASSERT ∃k: aₖ ≤ s ∧ e ≤ bₖ             // 验证通信窗口
  RETURN Plan""")
    doc.add_paragraph()

    # 2.6.8
    doc.add_heading('2.6.8 复杂度分析', level=3)

    p = doc.add_paragraph(); br(p, '表2-2 算法各阶段时间复杂度')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    htb(doc, ['阶段', '核心算法', '时间复杂度', '说明'],
        [['BUILD_STN', 'Bellman-Ford', 'O(VE)', 'V为时间点数, E为边数'],
         ['INC_PROPAGATE(添加)', 'Johnson+Dijkstra', 'O((V+E)log V)', '每次决策后'],
         ['INC_PROPAGATE(删除)', 'BF+Dijkstra', 'O(VE+(V+E)log V)', '回溯时'],
         ['SELECT_FLAW', '线性扫描', 'O(|Flaws|)', '缺陷遍历'],
         ['完整求解', 'S次迭代', 'O(S·(V+E)log V)', 'S为搜索步数']])
    doc.add_paragraph()

    # ════════════════════════════════════════
    # 2.7
    # ════════════════════════════════════════
    doc.add_heading('2.7 本章小结', level=2)

    doc.add_paragraph(
        '本章对空间站机械臂在轨作业任务规划问题进行了系统的形式化建模与求解算法设计。'
        '首先（2.1节），概述了问题的核心挑战：通信窗口周期性中断、遮挡约束的空间耦合、'
        '跨圈次提前量要求和任务时长超窗口容量。'
        '其次（2.2节），以五个形式化定义建立了时间线规划系统的数学框架：'
        'TPS五元组（定义1）→ 部分计划（定义2）→ 缺陷分类（定义3）→ STN约束网络（定义4）'
        '→ 规划问题（定义5），各定义按逻辑递进排列，每个定义建立在前一个之上。'
        '再次（2.3节），对四类约束进行了统一的数学建模，给出了6个约束公式（公式6-12）。'
        '然后（2.4-2.5节），使用NDDL声明式语言完成建模编码，给出了时间线类定义和动作规则的映射方式。'
        '最后（2.6节），给出了8个关键算法的伪代码，形成从NDDL输入到可执行计划输出的完整求解流程。'
        '其中STN增量Dijkstra传播（算法5-7）将单次约束推理控制在O((V+E)log V)，'
        '使得包含约200步搜索的完整求解在亚秒级时间内完成。')

    # Save
    for path in [f'{OUT}/chapter2_complete.docx',
                 '/workspace/documentation/chapter2_complete.docx']:
        doc.save(path)
    print(f'Saved: {path}')

if __name__ == '__main__':
    create()
