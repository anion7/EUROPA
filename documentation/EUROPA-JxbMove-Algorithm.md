# EUROPA 求解 JxbMove 的算法伪代码

## 1. 总体架构

EUROPA 使用 **缺陷导向的时序回溯搜索（Flaw-Directed Chronological Backtracking Search）** 算法。求解器不是前向模拟，而是从一个包含目标和初始状态的**不完整部分计划**出发，反复 (1) 发现缺陷、(2) 做出决策修复缺陷、(3) 传播约束检查一致性、(4) 不一致时回溯。

```
输入:
  - 初始状态: Arm.AtBase1(start=0), CommWindow facts, Occlusion facts
  - 目标: Arm.AtBase3(locId=5)
  - 求解器配置: ThreatManager, OpenConditionManager, UnboundVariableManager

输出:
  - 完整计划: 所有 Token 被激活/合并/排列，无缺陷
```

---

## 2. 主求解循环

```
算法: EUROPA_SOLVE(plan_database, max_steps, max_depth)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  decision_stack ← 空栈
  step_count ← 0
  active_decision ← null
  exhausted ← false
  no_flaws ← false

  WHILE NOT exhausted AND NOT no_flaws AND step_count < max_steps:

    // ──── 第一步: 约束传播 ────
    PROPAGATE(plan_database.constraint_engine)
    IF 不一致:
      exhausted ← true
      BREAK

    // ──── 第二步: 选择缺陷 ────
    IF active_decision = null:
      active_decision ← ALLOCATE_DECISION_POINT(plan_database)
    
    IF active_decision = null:
      no_flaws ← true    // 无缺陷 → 求解成功！
      BREAK

    // ──── 第三步: 执行决策 ────
    IF active_decision.has_next_choice():
      active_decision.EXECUTE()       // 应用选中的方案到计划
      PROPAGATE(constraint_engine)    // 传播新约束
      step_count ← step_count + 1

      IF 一致:
        decision_stack.PUSH(active_decision)
        active_decision ← null        // 进入下一轮
        CONTINUE
      ELSE:
        // 不一致 → 需要回溯
    ELSE:
      // 无更多选择 → 需要回溯

    // ──── 第四步: 回溯 ────
    exhausted ← BACKTRACK(active_decision, decision_stack)

  RETURN no_flaws
```

---

## 3. 缺陷选择算法

```
算法: ALLOCATE_DECISION_POINT(plan_database)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  // 优先处理零承诺决策（只有一个选择的缺陷）
  FOR EACH flaw_manager IN [ThreatMgr, OpenCondMgr, UnboundVarMgr]:
    decision ← flaw_manager.NEXT_ZERO_COMMITMENT()
    IF decision ≠ null:
      decision.INITIALIZE()
      RETURN decision

  // 否则，选择最高优先级的缺陷
  best_decision ← null
  best_priority ← +∞

  FOR EACH flaw_manager IN [ThreatMgr, OpenCondMgr, UnboundVarMgr]:
    candidate ← flaw_manager.NEXT(best_priority)
    IF candidate ≠ null AND candidate.priority < best_priority:
      best_decision ← candidate
      best_priority ← candidate.priority

  IF best_decision ≠ null:
    best_decision.INITIALIZE()
  RETURN best_decision
```

```
算法: FlawManager.NEXT(best_priority)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  best_flaw ← null
  best_p ← best_priority

  FOR EACH entity IN CREATE_ITERATOR():
    IF DYNAMIC_MATCH(entity):     // 被过滤器排除
      CONTINUE
    priority ← GET_PRIORITY(entity)
    IF priority < best_p:
      best_flaw ← entity
      best_p ← priority
    ELSE IF priority ≈ best_p AND BETTER_THAN(entity, best_flaw):
      best_flaw ← entity

  IF best_flaw ≠ null:
    handler ← GET_FLAW_HANDLER(best_flaw)
    RETURN handler.CREATE_DECISION_POINT(best_flaw)
  RETURN null
```

---

## 4. 三类缺陷及其决策

### 4.1 开放条件（OpenCondition）

**缺陷**: 未激活的 Token（状态为 INACTIVE）。

**对于 JxbMove**: 初始目标 `Arm.AtBase3` 是 INACTIVE 状态。

```
算法: OpenConditionDecisionPoint.INITIALIZE()
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  token ← 被标记为缺陷的 Token
  choices ← []

  // 选择 1: 合并（MERGE）— 是否存在兼容的已激活 Token？
  compatible_tokens ← plan_database.GET_COMPATIBLE_TOKENS(token)
  IF |compatible_tokens| > 0:
    choices.ADD(MERGE, compatible_tokens)

  // 选择 2: 激活（ACTIVATE）— 将 Token 放置到时间线上
  IF ACTIVE ∈ token.state_domain:
    choices.ADD(ACTIVATE)

  // 选择 3: 拒绝（REJECT）— 排除此可能性
  IF REJECTED ∈ token.state_domain:
    choices.ADD(REJECT)
```

```
算法: OpenConditionDecisionPoint.EXECUTE()
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  choice ← choices[current_index]

  CASE choice OF:
    ACTIVATE:
      plan_database.ACTIVATE(token)
      // → Token 放置到时间线上
      // → 触发规则引擎: 如果 Token 是 Move 动作，
      //   规则自动创建子 Token（met_by At, meets At, contained_by InComms）
      // → 新的子 Token 成为新的 OpenCondition 缺陷

    MERGE(target):
      plan_database.MERGE(token, target)
      // → Token 与已存在的 Token 统一
      // → 约束自动传播

    REJECT:
      plan_database.REJECT(token)
      // → 排除此 Token
```

```
算法: OpenConditionDecisionPoint.UNDO()
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  plan_database.CANCEL(token)  // 撤销激活/合并/拒绝
  IF choice = MERGE:
    merge_index ← merge_index + 1
    IF merge_index ≥ |compatible_tokens|:
      choice_index ← choice_index + 1  // 尝试下一类选择
  ELSE:
    choice_index ← choice_index + 1
```

### 4.2 时序威胁（Threat）

**缺陷**: 时间线上有 Token 需要排序（确定前后关系）。

**对于 JxbMove**: 当多个 Token 被激活到同一条时间线（如 `Arm`），它们之间的时序关系未确定。

```
算法: ThreatDecisionPoint.INITIALIZE()
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  token ← 需要排序的 Token
  choices ← timeline.GET_ORDERING_CHOICES(token)
  // 每个选择是一个 (predecessor, successor) 对
  // 表示将 token 插入到 predecessor 之后、successor 之前
  
  // 时间线排序算法:
  //   1. 如果时间线为空: choices = [(token, token)]
  //   2. 否则遍历现有序列的每个间隙:
  //      FOR EACH gap (pred, succ) IN timeline.sequence:
  //        IF temporal_network.CAN_FIT_BETWEEN(token, pred, succ):
  //          choices.ADD((pred, succ))
  //      IF token 可以放在最前面: choices.ADD((token, first))
  //      IF token 可以放在最后面: choices.ADD((last, token))
```

```
算法: ThreatDecisionPoint.EXECUTE()
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  (predecessor, successor) ← choices[current_index]
  timeline.CONSTRAIN(token, predecessor, successor)
  // → 添加时序约束: predecessor.end ≤ token.start
  // → 添加时序约束: token.end ≤ successor.start
  // → 约束传播: 时序网络更新所有时间变量的上下界
```

```
算法: ThreatDecisionPoint.UNDO()
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  timeline.FREE(token, predecessor, successor)
  current_index ← current_index + 1  // 尝试下一个排序方案
```

### 4.3 未绑定变量（UnboundVariable）

**缺陷**: 已激活 Token 的参数变量域未收窄为单值。

**对于 JxbMove**: 被 `InfiniteDynamicFilter` 和 `var-match` 过滤器排除了 `start`、`end`、`duration` 变量。只有非时序参数（如 `locId`、`fromLoc`、`toLoc`）在需要时被作为缺陷。

```
算法: UnboundVariableDecisionPoint.EXECUTE()
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  value ← GET_NEXT_VALUE()    // 从变量域中选取下一个候选值
  plan_database.SPECIFY(variable, value)
  // → 约束传播: 所有引用此变量的约束重新计算
```

```
算法: UnboundVariableDecisionPoint.UNDO()
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  plan_database.RESET(variable)   // 恢复变量域
  // 下次 EXECUTE 将选取域中的下一个值
```

---

## 5. 回溯算法

```
算法: BACKTRACK(active_decision, decision_stack)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  backtracking ← true

  WHILE backtracking AND (active_decision ≠ null OR decision_stack 非空):

    // 如果没有活跃决策，从栈中弹出一个
    IF active_decision = null AND decision_stack 非空:
      active_decision ← decision_stack.POP()

    // 撤销已执行的决策
    IF active_decision.is_executed():
      active_decision.UNDO()
      // → 撤销对计划数据库的修改
      // → 约束网络自动回退

    // 检查是否还有其他选择
    IF active_decision.HAS_NEXT() AND NOT active_decision.CUT():
      backtracking ← false      // 找到了可以继续的分支！
    ELSE:
      DELETE active_decision     // 彻底放弃此决策
      active_decision ← null    // 继续向上回溯

  RETURN backtracking    // true = 搜索空间耗尽
```

---

## 6. 约束传播算法

```
算法: PROPAGATE(constraint_engine)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  REPEAT:
    changed ← false
    
    // 按优先级执行传播器
    FOR EACH propagator IN [TemporalPropagator, DefaultPropagator, ...]:
      IF propagator.agenda 非空:
        FOR EACH constraint IN propagator.agenda:
          // 执行约束: 收窄相关变量的域
          constraint.HANDLE_EXECUTE()
          
          IF 任何变量域变为空:
            RETURN INCONSISTENT     // 矛盾！
          
          IF 任何变量域发生了变化:
            changed ← true
            // 将引用被修改变量的其他约束加入议程

  UNTIL NOT changed    // 到达不动点

  RETURN CONSISTENT
```

**时序传播器特殊处理**:

```
TemporalPropagator 维护一个 简单时序网络 (STN):
  - 每个时序变量（start, end, duration）对应一个时间点
  - 每个时序约束对应一条距离边
  - 使用增量 Dijkstra 算法传播距离界

关键约束类型:
  meets(A, B):           A.end = B.start
  met_by(A, B):          B.end = A.start  
  contained_by(A, B):    B.start ≤ A.start AND A.end ≤ B.end
  eq(duration, N):       end - start = N
```

---

## 7. 规则引擎触发

```
算法: RULE_ENGINE.ON_TOKEN_ACTIVATED(token)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  FOR EACH rule IN schema.GET_RULES(token.predicate):
    rule_instance ← rule.CREATE_INSTANCE(token)

    // 检查守卫变量（if 条件）
    IF rule_instance.GUARDS_SATISFIED():
      rule_instance.EXECUTE()
      // → 创建 Slave Token（子目标）
      // → 添加时序约束（meets, met_by, contained_by 等）
      // → 添加参数约束（eq 等）
      // → 新 Token 初始为 INACTIVE → 成为新的 OpenCondition 缺陷
```

**JxbMove 的 MoveToBase2 规则触发示例**:

```
当 Arm::MoveToBase2 被 ACTIVATE 时:
  → eq(duration, 203)                          // 固定时长
  → met_by(condition object.AtOn900Base2)       // 创建前置条件 Token
  → meets(effect object.AtBase2)                // 创建后置效果 Token
  → contained_by(condition object.comm.InComms) // 创建通信约束 Token

这些新 Token 成为新的 OpenCondition 缺陷，进入下一轮求解。
```

---

## 8. JxbMove 完整求解过程

以下展示 EUROPA 求解 JxbMove 的**完整决策序列**（45步）:

```
初始状态:
  Arm 时间线:  [AtBase1(start=0)] ··· [AtBase3(INACTIVE, locId=5)]
  CommWindow:  [InComms(0,660)] [OutComms(660,690)] [InComms(690,1200)] ...
  Occlusion:   [Inactive(0,690)] [Active(690,720)] [Inactive(720,1500)] ...
  缺陷: 1 个 OpenCondition (AtBase3 是 INACTIVE)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: OpenCondition → ACTIVATE AtBase3
  → AtBase3 放置到 Arm 时间线
  → 无规则触发（AtBase3 是 predicate，不是 action）
  新缺陷: Threat(AtBase3 需要在 Arm 时间线上排序)

Step 2: Threat → 将 AtBase3 排在 AtBase1 之后
  → 添加约束: AtBase1.end ≤ AtBase3.start
  新缺陷: 无新缺陷（但目标仍未达成，需要 Move 动作连接）

  ... 此时 AtBase3 的 locId=5 无法通过任何方式从 AtBase1(locId=1) 直接到达。
  求解器需要发现 MoveToBase3 action 来满足 met_by 条件。

Step 3-4: OpenCondition → ACTIVATE MoveToBase3
  → 规则触发:
    eq(duration, 203)
    met_by(condition Arm.AtOn900Base3)    → 创建新 INACTIVE Token
    meets(effect Arm.AtBase3)             → 合并到已存在的 AtBase3
    contained_by(condition CommWindow.InComms) → 创建新 INACTIVE Token
  新缺陷:
    - OpenCondition: AtOn900Base3 (INACTIVE)
    - OpenCondition: InComms (INACTIVE, 需要合并到已有窗口)
    - Threat: MoveToBase3 在 Arm 时间线上排序

Step 5-6: OpenCondition → MERGE InComms 到 comm3(1500,2900)
  → 添加约束: 1500 ≤ MoveToBase3.start AND MoveToBase3.end ≤ 2900
  → 传播: MoveToBase3.start ∈ [1500, 2697], end ∈ [1703, 2900]

Step 7-8: Threat → MoveToBase3 排在 AtBase1 之后
  → AtBase1.end ≤ MoveToBase3.start

Step 9-10: OpenCondition → ACTIVATE AtOn900Base3
  新缺陷: Threat (排序)

Step 11-12: Threat → AtOn900Base3 排在 MoveToBase3 之前

Step 13-14: OpenCondition → ACTIVATE MoveToOn900Base3
  → 规则触发:
    eq(duration, 583)
    met_by(condition Arm.AtBase2)
    meets(effect Arm.AtOn900Base3) → 合并
    contained_by(condition CommWindow.InComms)
    contained_by(condition OcclusionBase2.Inactive)  ← base2 遮挡约束！
  新缺陷: AtBase2, InComms(需合并), Inactive(需合并)

Step 15-16: MERGE InComms 到 comm3(1500,2900)
  → 1500 ≤ MoveToOn900Base3.start
  → MoveToOn900Base3.end ≤ 2900

Step 17-18: MERGE Inactive 到 occ_off3(1650,3000)
  → 1650 ≤ MoveToOn900Base3.start    ← 关键约束！
  → 传播: MoveToOn900Base3.start ∈ [1650, 2113]

Step 19-20: ACTIVATE AtBase2, 排序

Step 21-22: ACTIVATE MoveToBase2
  → eq(duration, 203)
  → met_by AtOn900Base2, meets AtBase2, contained_by InComms

Step 23-24: MERGE InComms → 尝试 comm1(0,660)
  → 传播: MoveToBase2.end ≤ 660
  → 但 MoveToBase2.start ≥ AtBase1.end ≥ 0, duration=203
  → 且 MoveToBase2 后面的 AtBase2 需要在 1650 前结束
  → 可能不一致 → 回溯!

Step 25-29: 回溯，MERGE InComms → 尝试 comm2(690,1200)
  → 690 ≤ MoveToBase2.start ≤ 997
  → MoveToBase2.end ∈ [893, 1200]
  → 一致!

Step 30-32: ACTIVATE AtOn900Base2, 排序

Step 33-34: ACTIVATE MoveToOn900Base2
  → eq(duration, 523)
  → met_by AtBase1, meets AtOn900Base2, contained_by InComms

Step 35-36: MERGE InComms → 尝试 comm1(0,660)
  → MoveToOn900Base2.start ∈ [0, 137]
  → MoveToOn900Base2.end ∈ [523, 660]
  → 一致!

Step 37-44: 剩余的 Threat 排序决策
  → 确定 Arm 时间线上所有 Token 的最终顺序

Step 45: 无更多缺陷 → 求解成功!

最终 Arm 时间线:
  AtBase1[0,137] → MoveToOn900Base2[137,660] → AtOn900Base2[660,690]
  → MoveToBase2[690,893] → AtBase2[893,1650]
  → MoveToOn900Base3[1650,2233] → AtOn900Base3[2233,2436]
  → MoveToBase3[2436,2639] → AtBase3[2639,3000]
```

---

## 9. 算法复杂度分析

| 方面 | 分析 |
|------|------|
| **搜索空间** | 每个 OpenCondition 有 ≤3 类选择（MERGE/ACTIVATE/REJECT），MERGE 有 O(n) 个兼容 Token |
| **时间线排序** | 每个 Threat 有 O(n) 个排序位置（n = 时间线上已有 Token 数） |
| **约束传播** | 每步 O(C) 其中 C 为约束数量；时序网络传播为 O(N²) 其中 N 为时间点数 |
| **回溯** | 最坏情况指数级，但约束传播大幅剪枝 |
| **JxbMove 实际** | 45 步完成，因为问题结构良好且约束传播高效 |

---

## 10. 关键设计特点

1. **缺陷驱动**: 不像传统前向搜索逐步构建计划，而是从不完整计划出发修复缺陷
2. **约束传播剪枝**: 每次决策后立即传播，尽早发现不一致，避免无效搜索
3. **时序网络**: STN 增量传播确保时间约束始终一致
4. **规则链式触发**: 激活一个 Move → 自动创建前置条件和后置效果 → 产生新缺陷 → 驱动进一步求解
5. **零承诺优先**: 只有一个选择的缺陷优先处理，减少搜索分支
6. **时间线排序**: Timeline 类强制 Token 不重叠，自动生成排序选择
