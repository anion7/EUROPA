#!/usr/bin/env python3
"""
Generate Word document: EUROPA formal modeling and solving for robotic arm task planning.
Follows the FSS/UPP style: formal definitions → algorithm pseudocode → solving pipeline.
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn

def shd(cell, color):
    pr = cell._element.get_or_add_tcPr()
    pr.append(pr.makeelement(qn('w:shd'), {qn('w:val'):'clear',qn('w:color'):'auto',qn('w:fill'):color}))

def htb(doc, hd, rows):
    t = doc.add_table(rows=1+len(rows), cols=len(hd), style='Table Grid')
    for i, h in enumerate(hd):
        c = t.rows[0].cells[i]; c.text = h; c.paragraphs[0].runs[0].bold = True; shd(c, 'D9E2F3')
    for ri, row in enumerate(rows):
        for ci, v in enumerate(row): t.rows[ri+1].cells[ci].text = str(v)

def code(doc, text):
    for ln in text.strip().split('\n'):
        p = doc.add_paragraph(); p.style = doc.styles['code']; p.add_run(ln)

def formula(doc, text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text); r.italic = True; return p

def bold_text(p, text):
    r = p.add_run(text); r.bold = True; return r

def create():
    doc = Document()
    s = doc.styles['Normal']; s.font.name = 'Times New Roman'; s.font.size = Pt(12)
    s.paragraph_format.line_spacing = 1.5; s.paragraph_format.space_after = Pt(6)
    rPr = s.element.get_or_add_rPr()
    rPr.append(rPr.makeelement(qn('w:rFonts'), {qn('w:eastAsia'): '宋体'}))
    for lv in range(1, 4):
        h = doc.styles[f'Heading {lv}']; h.font.color.rgb = RGBColor(0, 0, 0)
        h.font.bold = True; h.font.size = Pt([0, 16, 14, 12][lv])
    cs = doc.styles.add_style('code', WD_STYLE_TYPE.PARAGRAPH)
    cs.font.name = 'Consolas'; cs.font.size = Pt(9)
    cs.paragraph_format.space_before = Pt(0); cs.paragraph_format.space_after = Pt(0)
    cs.paragraph_format.line_spacing = 1.15; cs.paragraph_format.left_indent = Cm(1)

    # ════════════════════════════════════════
    title = doc.add_heading('第X章 基于EUROPA的机械臂作业规划建模与求解', level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(
        '空间站机械臂在轨作业任务规划问题涉及离散的任务状态转换与连续的时序约束推理。'
        '为有效求解此类混合特性问题，本章采用EUROPA框架的时间线规划范式对问题进行形式化建模，'
        '并给出基于缺陷导向搜索与简单时序网络传播的完整求解算法。'
        '以下首先给出时间线规划系统的形式化定义，进而描述如何在此类系统上求解机械臂作业规划问题。')

    # ════════════════════════════════════════
    doc.add_heading('X.1 时间线规划系统的形式化定义', level=2)

    # Definition 1
    p = doc.add_paragraph()
    bold_text(p, '定义1（时间线规划系统）')
    doc.add_paragraph(
        '时间线规划系统（Timeline Planning System, TPS）𝒮 是一个五元组 (𝒪, ℒ, 𝒯, 𝒞, ℛ)，其中：')
    items = [
        '𝒪 = {o₁, o₂, …, oₘ} 为有限对象集合，每个对象 oᵢ 关联一条时间线 Lᵢ ∈ ℒ；',
        'ℒ = {L₁, L₂, …, Lₘ} 为时间线集合，每条时间线 Lᵢ 上的Token形成有序不重叠序列；',
        '𝒯 为Token类型集合，分为谓词（predicate）和动作（action）两类，'
        '每个Token τ 具有类型 type(τ)、起始时间 start(τ)、结束时间 end(τ) 和持续时间 dur(τ) = end(τ) − start(τ)；',
        '𝒞 为约束集合，包含时序约束（定义在Token时间变量上的线性不等式）和参数约束（定义在Token参数变量上的等式/不等式）；',
        'ℛ 为规则集合，每条规则 r ∈ ℛ 关联一个Token类型，定义该类型Token被激活时自动创建的子Token和约束。',
    ]
    for item in items:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_paragraph(
        '时间线 Lᵢ 上的Token序列满足不重叠约束：对于同一时间线上的任意两个相邻Token τⱼ 和 τⱼ₊₁，'
        '有 end(τⱼ) ≤ start(τⱼ₊₁)。')

    # Definition 2
    p = doc.add_paragraph()
    bold_text(p, '定义2（部分计划）')
    doc.add_paragraph(
        '部分计划（Partial Plan）PP 是一个四元组 (Tokens, Active, Constraints, Flaws)，其中：')
    items2 = [
        'Tokens 为当前计划中所有Token的集合；',
        'Active ⊆ Tokens 为已激活（放置到时间线上）的Token子集；',
        'Constraints 为当前所有约束的集合，包含Token间的时序约束和参数约束；',
        'Flaws 为当前计划中的缺陷集合，Flaws = Flaws_OC ∪ Flaws_TH ∪ Flaws_UV，'
        '分别对应开放条件缺陷、时序威胁缺陷和未绑定变量缺陷（定义见下）。',
    ]
    for item in items2:
        doc.add_paragraph(item, style='List Bullet')

    # Definition 3
    p = doc.add_paragraph()
    bold_text(p, '定义3（缺陷）')
    doc.add_paragraph('部分计划中的缺陷分为三类：')
    items3 = [
        '开放条件（Open Condition）：Token τ ∈ Tokens \\ Active，即存在于计划中但尚未放置到时间线上的Token。'
        '解决策略集合 Choices_OC(τ) = {ACTIVATE, MERGE(τ, τ′) | τ′ ∈ Compatible(τ), REJECT}。',
        '时序威胁（Threat）：已激活Token τ ∈ Active 在其所属时间线上的排序未确定。'
        '解决策略集合 Choices_TH(τ) = {ORDER(τ, pred, succ) | canFitBetween(τ, pred, succ) = true}。',
        '未绑定变量（Unbound Variable）：已激活Token的参数变量 v 的域 Dom(v) 未收窄为单值。'
        '解决策略集合 Choices_UV(v) = {SPECIFY(v, d) | d ∈ Dom(v)}。',
    ]
    for item in items3:
        doc.add_paragraph(item, style='List Bullet')

    # Definition 4
    p = doc.add_paragraph()
    bold_text(p, '定义4（简单时序网络）')
    doc.add_paragraph(
        '简单时序网络（Simple Temporal Network, STN）N 是一个三元组 (V, E, O)，其中：')
    items4 = [
        'V = {v₁, v₂, …, vₙ} 为时间点集合，每个Token τ 贡献三个时间点 start(τ), end(τ), dur(τ)；',
        'E ⊆ V × V × ℝ 为有向加权边集合，边 (vᵢ, vⱼ, w) 表示约束 vⱼ − vᵢ ≤ w；',
        'O ∈ V 为参考原点，所有时间点的界相对于 O 定义。',
    ]
    for item in items4:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_paragraph(
        '时序约束 lb ≤ vⱼ − vᵢ ≤ ub 编码为两条边：(vᵢ, vⱼ, ub) 和 (vⱼ, vᵢ, −lb)。'
        '时间点 v 的上界 ub(v) = δ(O, v)（O到v的最短路径），下界 lb(v) = −δ(v, O)。'
        '若距离图中存在负权环路，则约束系统不一致。')

    # Definition 5
    p = doc.add_paragraph()
    bold_text(p, '定义5（机械臂作业规划问题）')
    doc.add_paragraph(
        '机械臂作业规划问题是TPS上的约束满足问题 𝒫 = (𝒮, s₀, 𝒢, H)，其中：')
    items5 = [
        '𝒮 = (𝒪, ℒ, 𝒯, 𝒞, ℛ) 为时间线规划系统（定义1），'
        '对象集合 𝒪 = {Arm, CommWindow, OcclusionSWA}；',
        's₀ 为初始部分计划，包含环境时间线上的Fact Token（通信窗口序列、遮挡状态序列）'
        '和Phase 1子任务的固定放置；',
        '𝒢 为目标条件，即Token Done 被激活且 start(Done) ≤ H；',
        'H 为规划范围上界。',
    ]
    for item in items5:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_paragraph(
        '问题的解是一个完整计划 PP*，满足：(1) Flaws(PP*) = ∅（无缺陷）；'
        '(2) 对所有已激活Token τ ∈ Active(PP*)，lb(start(τ)) ≤ ub(start(τ))（时序一致）；'
        '(3) 所有操作Token的时间区间被包含在某个通信窗口内（contained_by约束）。')

    # ════════════════════════════════════════
    doc.add_heading('X.2 求解算法', level=2)

    doc.add_paragraph(
        '求解算法分为三个阶段：约束网络构建、缺陷导向搜索、计划提取。'
        '以下分别给出各阶段的形式化描述和伪代码。')

    # Phase 1
    doc.add_heading('X.2.1 约束网络构建（BUILD_STN过程）', level=3)

    doc.add_paragraph(
        'BUILD_STN过程读入NDDL模型和问题实例，构建初始STN并验证一致性。'
        '该过程对应图X-1流程图中的Phase 1和Phase 2。')

    p = doc.add_paragraph(); bold_text(p, '算法1 BUILD_STN过程')
    code(doc, """
输入: NDDL域模型 M, 问题实例 P
输出: 初始STN N, 初始部分计划 PP₀

过程 BUILD_STN(M, P):
  Schema ← PARSE_NDDL(M)          // ANTLR3解析,注册类型/规则
  PP₀ ← INSTANTIATE(P, Schema)    // 创建对象,Fact/Goal Token
  N ← (V=∅, E=∅, O=origin)

  // 为每个Token创建STN时间点
  FOR EACH τ ∈ PP₀.Tokens:
    ADD_TIMEPOINT(N, start(τ))
    ADD_TIMEPOINT(N, end(τ))
    ADD_EDGE(N, start(τ), end(τ), dur(τ))    // end-start ≤ dur
    ADD_EDGE(N, end(τ), start(τ), -dur(τ))   // end-start ≥ dur

  // Fact Token的固定时间界
  FOR EACH τ ∈ PP₀.Facts:
    ADD_EDGE(N, O, start(τ), start_value(τ))
    ADD_EDGE(N, start(τ), O, -start_value(τ))

  // Bellman-Ford计算势函数
  consistent ← BELLMAN_FORD(N)
  IF ¬consistent: RETURN FAIL

  RETURN (N, PP₀)""")
    doc.add_paragraph()

    # Phase 2
    doc.add_heading('X.2.2 缺陷导向搜索（FLAW_DIRECTED_SEARCH过程）', level=3)

    doc.add_paragraph(
        'FLAW_DIRECTED_SEARCH是求解算法的核心，采用时序回溯搜索策略。'
        '该过程维护决策栈Stack记录已做出的决策，支持回溯时撤销。'
        '对应图X-1流程图中的Phase 3至Phase 7。')

    p = doc.add_paragraph(); bold_text(p, '算法2 FLAW_DIRECTED_SEARCH过程')
    code(doc, """
输入: 初始STN N, 初始部分计划 PP₀, 最大步数 N_max
输出: 完整计划 PP* 或 FAIL

过程 FLAW_DIRECTED_SEARCH(N, PP₀, N_max):
  Stack ← ∅;  PP ← PP₀;  n ← 0

  WHILE n < N_max:
    // 步骤1: 约束传播
    consistent ← INC_PROPAGATE(N)
    IF ¬consistent ∧ Stack = ∅: RETURN FAIL

    // 步骤2: 缺陷选择
    flaw ← SELECT_FLAW(PP)
    IF flaw = ∅: RETURN PP           // 无缺陷→成功

    // 步骤3: 决策生成
    dp ← CREATE_DECISION(flaw)
    dp.INITIALIZE()                   // 枚举可选方案

    // 步骤4: 决策执行
    choice ← dp.NEXT_CHOICE()
    APPLY(choice, PP, N)              // 修改PP和N
    n ← n + 1

    // 步骤5: 规则触发(若choice为ACTIVATE)
    IF choice.type = ACTIVATE:
      FOR EACH rule ∈ RULES(choice.token):
        FIRE_RULE(rule, PP, N)        // 创建子Token+约束

    // 步骤6: 传播+验证
    consistent ← INC_PROPAGATE(N)
    IF consistent:
      Stack.PUSH(dp)                  // 成功,入栈
    ELSE:
      // 步骤7: 回溯
      exhausted ← BACKTRACK(dp, Stack, PP, N)
      IF exhausted: RETURN FAIL

  RETURN TIMEOUT""")
    doc.add_paragraph()

    doc.add_paragraph(
        '其中SELECT_FLAW的选择策略为：优先处理仅有唯一解决方案的缺陷（零承诺决策），'
        '然后按缺陷管理器优先级（ThreatManager → OpenConditionManager → UnboundVariableManager）'
        '选择最高优先级缺陷。')

    # INC_PROPAGATE
    doc.add_heading('X.2.3 STN增量传播（INC_PROPAGATE过程）', level=3)

    doc.add_paragraph(
        'INC_PROPAGATE是保证求解效率的关键。当添加新约束时，算法仅传播受影响的局部网络，'
        '避免全量重计算。采用Johnson重标号技术处理负权边，使用桶排序优先队列实现O((V+E)log V)的传播复杂度。')

    p = doc.add_paragraph(); bold_text(p, '算法3 INC_PROPAGATE过程')
    code(doc, """
输入: STN N, 新约束边 (src, targ, weight)
输出: consistent ∈ {true, false}

过程 INC_PROPAGATE(N, src, targ):
  // 阶段1: 一致性检查(增量Bellman-Ford)
  IF RELAXABLE(src.π, targ.π, edge):
    consistent ← INC_BELLMAN_FORD(N)
    IF ¬consistent: RETURN false

  // 阶段2: 上界传播(增量Dijkstra前向)
  IF src.ub + edge.w < targ.ub:
    targ.ub ← src.ub + edge.w
    Queue.INSERT(targ)
    DIJKSTRA_FORWARD(N, Queue)        // 沿出边传播

  // 阶段3: 下界传播(增量Dijkstra后向)
  IF (-targ.lb) + edge.w < (-src.lb):
    src.lb ← -((-targ.lb) + edge.w)
    Queue.INSERT(src)
    DIJKSTRA_BACKWARD(N, Queue)       // 沿入边反向传播

  RETURN true""")
    doc.add_paragraph()

    # BACKTRACK
    doc.add_heading('X.2.4 时序回溯（BACKTRACK过程）', level=3)

    doc.add_paragraph(
        'BACKTRACK过程在约束不一致时执行，从决策栈顶开始逐层撤销决策，'
        '直到找到尚有可选分支的决策点。撤销决策时，STN中对应的约束边被移除，'
        '需执行完全重传播以恢复一致的约束状态。')

    p = doc.add_paragraph(); bold_text(p, '算法4 BACKTRACK过程')
    code(doc, """
输入: 当前决策 dp, 决策栈 Stack, 部分计划 PP, STN N
输出: exhausted ∈ {true, false}

过程 BACKTRACK(dp, Stack, PP, N):
  WHILE dp ≠ ∅ ∨ Stack ≠ ∅:
    IF dp = ∅: dp ← Stack.POP()

    IF dp.IS_EXECUTED():
      dp.UNDO(PP, N)                 // 撤销对PP和N的修改
      FULL_PROPAGATE(N)              // Bellman-Ford + 双向Dijkstra

    IF dp.HAS_NEXT_CHOICE():
      RETURN false                    // 找到替代分支
    ELSE:
      DELETE dp; dp ← ∅

  RETURN true                         // 搜索空间耗尽""")
    doc.add_paragraph()

    # Phase 3
    doc.add_heading('X.2.5 计划提取（EXTRACT_PLAN过程）', level=3)

    doc.add_paragraph(
        'EXTRACT_PLAN过程从求解完成的STN中提取每个Token的时间界，'
        '构造最早开始时间调度方案，并验证所有任务均在通信窗口内。')

    p = doc.add_paragraph(); bold_text(p, '算法5 EXTRACT_PLAN过程')
    code(doc, """
输入: 完整计划 PP*, STN N
输出: 可执行计划 Plan

过程 EXTRACT_PLAN(PP*, N):
  Plan ← ∅
  FOR EACH τ ∈ PP*.Active (按时间线顺序):
    s ← lb(start(τ))                 // STN下界=最早开始时间
    e ← s + dur(τ)
    Plan.ADD((type(τ), s, e, dur(τ)))

    // 验证通信窗口约束
    IF type(τ) ∈ OperationTypes:
      ASSERT ∃ window ∈ CommWindows: window.start ≤ s ∧ e ≤ window.end

  RETURN Plan""")
    doc.add_paragraph()

    # ════════════════════════════════════════
    doc.add_heading('X.3 求解流程', level=2)

    doc.add_paragraph(
        '图X-1给出了EUROPA求解机械臂作业规划问题的完整流程。')

    # Insert flowchart
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run()
    r.add_picture('/workspace/examples/experiment_final/europa_flowchart.png', width=Inches(5.0))
    p2 = doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.add_run('图X-1 EUROPA求解机械臂任务规划流程').italic = True
    doc.add_paragraph()

    doc.add_paragraph(
        '如图X-1所示，求解流程包含八个阶段。Phase 1读入NDDL声明式模型文件，'
        '通过ANTLR3解析器将其转换为内部表示，创建三条Timeline上的初始Token。'
        'Phase 2为所有Token的时间变量构建STN约束网络，通过Bellman-Ford计算初始势函数。'
        'Phase 3至Phase 6构成核心搜索循环：求解器反复执行约束传播、缺陷选择、决策执行、'
        '规则触发和一致性验证的五步迭代，其中Phase 4专门处理通信窗口的contained_by匹配，'
        'Phase 5处理SWA遮挡约束检查，Phase 6确定Timeline上Token的排列顺序。'
        '不一致时触发时序回溯（红色箭头），撤销决策并尝试替代分支。'
        'Phase 7验证提前量约束（大臂重启≥12h、小臂重启≥5h），'
        'Phase 8从STN中提取最早开始时间方案并生成可执行计划。')

    # ════════════════════════════════════════
    doc.add_heading('X.4 算法复杂度', level=2)

    p = doc.add_paragraph(); bold_text(p, '表X-1 算法各阶段复杂度')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    htb(doc, ['阶段', '算法', '时间复杂度', '说明'], [
        ['BUILD_STN', 'Bellman-Ford', 'O(VE)', '初始势函数计算，V为时间点数，E为边数'],
        ['INC_PROPAGATE(添加)', 'Johnson+Dijkstra', 'O((V+E)log V)', '增量传播，单次约束添加'],
        ['INC_PROPAGATE(删除)', 'Bellman-Ford+Dijkstra', 'O(VE+(V+E)log V)', '完全重传播，回溯时'],
        ['SELECT_FLAW', '线性扫描', 'O(F)', 'F为当前缺陷数'],
        ['BACKTRACK', '栈操作+重传播', 'O(D·VE)', 'D为回溯深度'],
        ['EXTRACT_PLAN', '线性扫描', 'O(T)', 'T为Token数'],
        ['完整求解', 'S次迭代', 'O(S·(V+E)log V)', 'S为搜索步数（本算例~200步）'],
    ])
    doc.add_paragraph()

    # ════════════════════════════════════════
    doc.add_heading('X.5 本章小结', level=2)

    doc.add_paragraph(
        '本章对基于EUROPA的机械臂作业规划问题进行了形式化建模与求解算法设计。'
        '首先，定义了时间线规划系统（TPS）的五元组形式，引入部分计划、缺陷、'
        '简单时序网络等核心概念，将机械臂作业规划形式化为TPS上的约束满足问题。'
        '其次，给出了五个关键算法的伪代码：BUILD_STN构建初始约束网络，'
        'FLAW_DIRECTED_SEARCH实现缺陷导向时序回溯搜索的核心循环，'
        'INC_PROPAGATE通过Johnson重标号和增量Dijkstra实现高效的约束传播，'
        'BACKTRACK实现时序回溯，EXTRACT_PLAN提取可执行计划。'
        '最后，通过流程图展示了从NDDL输入到计划输出的八阶段求解流程。'
        '与显式状态空间搜索方法（如UPMurphi的BUILD_GRAPH+UPLAN_GENERATION两阶段算法）相比，'
        'EUROPA的缺陷导向搜索直接在部分计划空间中操作，'
        '通过STN增量传播实现O((V+E)log V)的单步约束推理，'
        '避免了显式枚举可达状态空间的指数级开销，'
        '在长时间跨度的机械臂调度问题上具有显著的效率优势。')

    # Save
    for path in ['/opt/cursor/artifacts/europa_formalization.docx',
                 '/workspace/examples/experiment_final/europa_formalization.docx',
                 '/workspace/documentation/europa_formalization.docx']:
        doc.save(path)
    print(f'Saved: {path}')

if __name__ == '__main__':
    create()
