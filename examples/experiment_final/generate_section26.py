#!/usr/bin/env python3
"""
Generate section 2.6: EUROPA-based solving algorithm for robotic arm task planning.
Integrates the formalization content as section 2.6, following the reviewer's
suggestions: definitions describe "what", algorithms describe "how to do".
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn

def shd(cell, color):
    pr = cell._element.get_or_add_tcPr()
    pr.append(pr.makeelement(qn('w:shd'),{qn('w:val'):'clear',qn('w:color'):'auto',qn('w:fill'):color}))

def htb(doc, hd, rows):
    t = doc.add_table(rows=1+len(rows), cols=len(hd), style='Table Grid')
    for i, h in enumerate(hd):
        c = t.rows[0].cells[i]; c.text = h
        c.paragraphs[0].runs[0].bold = True; shd(c, 'D9E2F3')
    for ri, row in enumerate(rows):
        for ci, v in enumerate(row):
            t.rows[ri+1].cells[ci].text = str(v)

def code(doc, text):
    for ln in text.strip().split('\n'):
        p = doc.add_paragraph(); p.style = doc.styles['code']; p.add_run(ln)

def formula(doc, text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text); r.italic = True

def brun(p, text):
    r = p.add_run(text); r.bold = True; return r

OUT = '/workspace/examples/experiment_final'

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

    # ════════════════════════════════════════════
    doc.add_heading('2.6 空间站机械臂作业任务规划求解流程', level=2)

    doc.add_paragraph(
        '基于2.2节建立的时间线规划系统形式化模型和2.3节定义的约束体系，'
        '本节给出求解算法的完整流程。求解算法的核心是缺陷导向的时序回溯搜索'
        '（Flaw-Directed Temporal Backtracking Search），其基本思想是：'
        '从包含初始状态和目标的不完整部分计划出发，反复识别缺陷、做出修复决策、'
        '通过简单时序网络（STN）的增量传播验证一致性，不一致时回溯尝试替代方案，'
        '直至所有缺陷消除。')

    # ── 2.6.1 ──
    doc.add_heading('2.6.1 求解流程概述', level=3)

    doc.add_paragraph(
        '求解算法分为三个阶段：约束网络构建、缺陷导向搜索、计划提取。'
        '图2-X给出了完整的求解流程。')

    # Insert flowchart
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run()
    r.add_picture(f'{OUT}/europa_flowchart.png', width=Inches(4.5))
    p2 = doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.add_run('图2-X EUROPA求解机械臂任务规划流程').italic = True
    doc.add_paragraph()

    doc.add_paragraph(
        '如图2-X所示，Phase 1读入NDDL声明式模型文件，通过ANTLR3解析器创建三条'
        'Timeline（机械臂任务线、通信窗口线、遮挡状态线）上的初始Token（令牌）。'
        'Phase 2为所有Token的时间变量在STN中创建时间点节点，通过Bellman-Ford算法'
        '计算初始势函数并验证一致性。Phase 3至Phase 6构成核心搜索循环：求解器反复'
        '执行约束传播、缺陷选择、决策执行、规则触发和一致性验证的五步迭代，其中'
        'Phase 4处理通信窗口的包含约束（contained_by）匹配，Phase 5处理SWA遮挡约束检查，'
        'Phase 6确定Timeline上Token的排列顺序。不一致时触发时序回溯，撤销决策并'
        '尝试替代分支。Phase 7验证提前量约束（公式待引用），Phase 8从STN中提取'
        '最早开始时间方案并生成可执行计划。')

    # ── 2.6.2 ──
    doc.add_heading('2.6.2 约束网络构建（BUILD_STN）', level=3)

    doc.add_paragraph(
        'BUILD_STN过程读入NDDL模型和问题实例，构建初始STN并验证一致性。'
        '该过程对应图2-X中的Phase 1和Phase 2。根据定义4中STN的三元组结构 N = (V, E, O)，'
        '为每个Token的start、end、duration变量创建时间点节点，'
        '将时序约束按公式(16)编码为距离图中的有向边，'
        '并通过Bellman-Ford算法计算势函数π(v)以支持后续的增量Dijkstra传播。')

    p = doc.add_paragraph(); brun(p, '算法8 BUILD_STN过程')
    code(doc, """
输入: NDDL域模型 M, 问题实例 P
输出: 初始STN N, 初始部分计划 PP₀

过程 BUILD_STN(M, P):
  Schema ← PARSE_NDDL(M)             // ANTLR3解析, 注册类型/谓词/规则
  PP₀ ← INSTANTIATE(P, Schema)       // 创建对象, Fact/Goal Token
  N ← (V = ∅, E = ∅, O = origin)

  // 为每个Token创建STN时间点并添加持续时间约束
  FOR EACH τ ∈ PP₀.Tokens:
    ADD_TIMEPOINT(N, start(τ))
    ADD_TIMEPOINT(N, end(τ))
    // 编码 dur(τ) = end(τ) - start(τ), 即公式(16)中lb = ub = dur(τ)
    ADD_EDGE(N, start(τ), end(τ), dur(τ))      // 上界边
    ADD_EDGE(N, end(τ), start(τ), -dur(τ))     // 下界边

  // Fact Token的固定时间值 → STN约束
  FOR EACH τ ∈ PP₀.Facts:
    ADD_EDGE(N, O, start(τ), start_val(τ))
    ADD_EDGE(N, start(τ), O, -start_val(τ))

  // Bellman-Ford计算势函数π(v), 检测负环
  consistent ← BELLMAN_FORD(N)
  IF ¬consistent: RETURN FAIL

  RETURN (N, PP₀)""")
    doc.add_paragraph()

    # ── 2.6.3 ──
    doc.add_heading('2.6.3 缺陷导向搜索主循环（Solve）', level=3)

    doc.add_paragraph(
        'Solve过程是求解算法的核心，对应图2-X中Phase 3至Phase 7。'
        '该过程维护决策栈（Decision Stack）记录已做出的决策，支持回溯时撤销。'
        '每一步执行"传播—选缺陷—决策—验证—回溯"五步循环。')

    p = doc.add_paragraph(); brun(p, '算法2 Solve(partialPlan PP, maxSteps, maxDepth)（完善版）')

    doc.add_paragraph(
        '算法2的伪代码已在前文给出（见2.6节算法2）。此处对其中的关键步骤进行补充说明：')

    doc.add_paragraph(
        '（1）步骤1"约束传播"调用STN增量传播过程（算法5），通过Johnson重标号后的'
        '增量Dijkstra在O((V+E)log V)复杂度内传播约束变化。该过程分为三个阶段：'
        '一致性检查（增量Bellman-Ford）、上界传播（前向Dijkstra，算法6）和下界传播'
        '（后向Dijkstra，算法7）。增量传播的关键优化在于START_NODE函数执行的可行性预检：'
        '若新约束不能改进任一端点的距离值，则传播在O(1)内终止，避免无效的全图遍历。')

    doc.add_paragraph(
        '（2）步骤2"缺陷选择"由算法3（Allocate_Decision）实现。核心策略有两个层次：'
        '①零承诺优先——优先处理仅有唯一解决方案的缺陷（如规则触发创建的effect Token'
        '只能合并到特定Fact），此类决策不引入搜索分支，可无代价地推进求解；'
        '②优先级排序——在多个缺陷中按缺陷管理器的配置优先级'
        '（ThreatManager → OpenConditionManager → UnboundVariableManager）和缺陷自身的紧急度综合排序。')

    doc.add_paragraph(
        '（3）步骤3"执行决策"根据缺陷类型（定义3）选择相应操作：'
        '对开放条件缺陷执行ACTIVATE（激活Token到时间线，触发规则引擎创建子Token和约束）、'
        'MERGE（与已有兼容Token合并）或REJECT（排除可能性）；'
        '对时序威胁缺陷执行ORDER（选择排序位置）；'
        '对未绑定变量缺陷执行SPECIFY（从变量域中选取值）。'
        '其中ACTIVATE操作会触发规则引擎：对于每条关联规则 r ∈ ℛ(type(τ))，'
        '自动创建met_by、meets、contained_by等子Token和相应的STN约束边，'
        '这些新创建的子Token以INACTIVE状态进入计划，成为新的开放条件缺陷，'
        '驱动求解器继续反向链式推理。')

    doc.add_paragraph(
        '（4）步骤5"回溯"由算法4（Backtrack）实现。当约束传播检测到不一致时，'
        '从决策栈顶开始逐层撤销决策，直到找到尚有可选分支的决策点。'
        '撤销决策时，该决策添加到STN中的约束边被移除，所有受影响的Token恢复到决策前的状态。'
        '由于约束删除可能使之前被排除的路径重新可行，STN需执行完全重传播'
        '（Bellman-Ford + 双向Dijkstra），这是回溯代价的主要来源。')

    # ── 2.6.4 ──
    doc.add_heading('2.6.4 通信窗口匹配与遮挡约束处理', level=3)

    doc.add_paragraph(
        '通信窗口匹配是求解过程中搜索分支的主要来源。当某个操作Token τ 的规则体'
        '包含contained_by(InComms)约束时，规则引擎创建一个InComms子Token（INACTIVE状态）。'
        '该子Token成为开放条件缺陷，求解器通过MERGE操作将其与环境时间线上已有的'
        'InComms Fact Token合并。每个Fact窗口构成一个可选的合并目标，'
        '合并后STN传播自动添加约束：')

    formula(doc, 'window.start ≤ τ.start  ∧  τ.end ≤ window.end')

    doc.add_paragraph(
        '若传播后STN检测到不一致（如窗口容量不足以容纳任务时长），'
        '则回溯并尝试下一个InComms窗口。通信窗口数量直接决定了此处的搜索分支数。')

    doc.add_paragraph(
        '对于SWA附近的操作（Phase 4和Phase 5），除通信窗口约束外还需满足遮挡回避约束。'
        '规则体中的contained_by(Inactive)约束以相同的机制处理：创建Inactive子Token，'
        'MERGE到遮挡状态时间线的Inactive Fact，STN传播收窄任务时间界。'
        '当通信窗口内存在遮挡事件时（如算例二中Vis11窗口内的遮挡区间[61750, 62180]），'
        '两个contained_by约束的联合传播将检测到矛盾，迫使求解器将任务推迟至'
        '下一个同时满足通信可用和遮挡不活跃的窗口。')

    # ── 2.6.5 ──
    doc.add_heading('2.6.5 STN增量传播', level=3)

    doc.add_paragraph(
        'STN增量传播是保证求解效率的关键机制。如2.2节定义4所述，STN以有向加权距离图'
        '维护所有时间变量之间的约束关系。由于下界边的权重为负值（公式16），'
        '标准Dijkstra算法不可直接使用。本算法采用Johnson重标号技术：'
        '首先通过Bellman-Ford算法计算每个节点的势函数π(v)，然后将边权重标号为：')

    formula(doc, "w'(u, v) = w(u, v) + π(u) − π(v) ≥ 0        (18)")

    doc.add_paragraph(
        '重标号后所有边权非负，可使用Dijkstra算法进行高效传播。'
        '增量传播（算法5）在添加一条新约束时分三个阶段执行：')

    items = [
        '阶段1——一致性检查：通过增量Bellman-Ford检测新约束是否引入负环（矛盾）。',
        '阶段2——上界传播（算法6，前向Dijkstra）：沿出边方向传播，更新受影响节点的upperBound。'
        '使用Johnson重标号后的非负键值 key = newDist − π(next) 作为优先队列的排序依据。',
        '阶段3——下界传播（算法7，后向Dijkstra）：沿入边反向传播，更新受影响节点的lowerBound。'
        '下界以负值编码：传播 (−lowerBound) 沿入边方向的最短路径。',
    ]
    for item in items:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_paragraph(
        '增量传播的核心优化在于START_NODE函数：检测新边是否能改进某个端点的距离值，'
        '若不能改进则传播在O(1)内终止。对于本算例（约80个时间点、160条边），'
        '每次增量传播的实际耗时在微秒量级。')

    # ── 2.6.6 ──
    doc.add_heading('2.6.6 计划提取与验证', level=3)

    doc.add_paragraph(
        '当搜索循环终止（Flaws = ∅）时，从STN中提取每个已激活Token的时间界，'
        '取最早开始时间（lowerBound）构造可执行的任务计划。')

    p = doc.add_paragraph(); brun(p, '算法9 EXTRACT_PLAN过程')
    code(doc, """
输入: 完整计划 PP*, STN N
输出: 可执行计划 Plan

过程 EXTRACT_PLAN(PP*, N):
  Plan ← ∅
  FOR EACH τ ∈ PP*.Active (按时间线顺序):
    s ← lb(start(τ))          // STN下界 = 最早开始时间
    e ← s + dur(τ)
    Plan.ADD( (type(τ), s, e, dur(τ)) )

    // 验证通信窗口约束(定义5条件3)
    IF type(τ) ∈ OperationTypes:
      ASSERT ∃ k ∈ {1,...,m}: aₖ ≤ s ∧ e ≤ bₖ

    // 验证提前量约束
    IF type(τ) = BigArmRestart:
      ASSERT e + 43200 ≤ start(Phase3)
    IF type(τ) = SmallArmRestart:
      ASSERT e + 18000 ≤ start(Phase4)

  RETURN Plan""")
    doc.add_paragraph()

    # ── 2.6.7 ──
    doc.add_heading('2.6.7 算法复杂度分析', level=3)

    p = doc.add_paragraph(); brun(p, '表2-X 算法各阶段时间复杂度')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    htb(doc, ['阶段', '核心算法', '时间复杂度', '说明'], [
        ['BUILD_STN', 'Bellman-Ford', 'O(VE)', '初始势函数计算'],
        ['INC_PROPAGATE(添加)', 'Johnson + Dijkstra', 'O((V+E)log V)', '增量传播，每次决策后'],
        ['INC_PROPAGATE(删除)', 'Bellman-Ford + Dijkstra', 'O(VE + (V+E)log V)', '完全重传播，回溯时'],
        ['SELECT_FLAW', '线性扫描', 'O(|Flaws|)', '缺陷遍历与优先级排序'],
        ['BACKTRACK', '栈操作 + 重传播', 'O(D · VE)', 'D为回溯深度'],
        ['EXTRACT_PLAN', '线性扫描', 'O(|Active|)', 'Token遍历与验证'],
        ['完整求解', 'S次迭代', 'O(S · (V+E)log V)', 'S为搜索步数'],
    ])
    doc.add_paragraph()

    doc.add_paragraph(
        '其中V为STN时间点数，E为约束边数，S为搜索步数。对于本文的机械臂算例，'
        'V ≈ 80，E ≈ 160，S ≈ 200，完整求解在亚秒级时间内完成。'
        '与显式状态空间搜索方法（如UPMurphi的BUILD_GRAPH过程）相比，'
        'EUROPA的缺陷导向搜索直接在部分计划空间中操作，通过STN增量传播实现'
        '高效的约束推理，避免了显式枚举可达状态空间的指数级开销。')

    # ── 2.6.8 ──
    doc.add_heading('2.6.8 本节小结', level=3)

    doc.add_paragraph(
        '本节给出了基于EUROPA框架的机械臂作业规划求解算法的完整流程。'
        '算法包含两个新增伪代码（算法8 BUILD_STN和算法9 EXTRACT_PLAN），'
        '与前文已给出的算法2-7共同构成完整的求解体系。'
        '算法的核心特点包括：'
        '（1）缺陷导向搜索从不完整部分计划出发，通过修复缺陷逐步精化，'
        '避免了前向搜索的状态爆炸问题；'
        '（2）规则驱动的反向链式推理自动构建因果链，从目标反向推导出所有必要的前置任务；'
        '（3）STN增量Dijkstra传播将单次约束添加的推理控制在O((V+E)log V)，'
        '使得每步决策后的约束验证在微秒级完成；'
        '（4）通信窗口和遮挡约束通过contained_by时序关系自然融入搜索框架，'
        '约束冲突时的自动回溯实现了遮挡回避的规划能力。')

    # Save
    for path in [f'{OUT}/section_2_6.docx',
                 '/workspace/documentation/section_2_6.docx']:
        doc.save(path)
    print(f'Saved: {path}')

if __name__ == '__main__':
    create()
