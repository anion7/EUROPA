# EUROPA 简单时序网络 (STN) 增量 Dijkstra 算法详解

## 1. STN 在 EUROPA 中的角色

EUROPA 的时序推理由三层架构驱动：

```
┌────────────────────────┐
│   约束引擎 (CE)         │  ← 管理所有变量域和约束
│   IntervalIntDomain     │     每个时序变量有 [lb, ub] 域
├────────────────────────┤
│   时序传播器             │  ← CE 与 STN 之间的桥梁
│   TemporalPropagator   │     同步变量域 ↔ 时间点界
├────────────────────────┤
│   简单时序网络 (STN)     │  ← 距离图 + Dijkstra 传播
│   TemporalNetwork      │     增量维护所有时间点的上下界
│   ← DistanceGraph      │
└────────────────────────┘
```

**关键思想**: 时序约束 `lb ≤ B - A ≤ ub` 被编码为距离图中的两条边：
- A → B，权重 `ub`（B 最多比 A 晚 ub 个时间单位）
- B → A，权重 `-lb`（B 最少比 A 晚 lb 个时间单位）

**时间点的界**: 每个时间点 T 相对于原点 O 有：
- `upperBound` = O 到 T 的最短路径长度（T 最晚可能的时刻）
- `lowerBound` = -(T 到 O 的最短路径长度)（T 最早可能的时刻）

---

## 2. 数据结构

```
结构体 Timepoint (继承自 Dnode):
  upperBound: Time      // 上界（最晚时刻）
  lowerBound: Time      // 下界（最早时刻）
  potential:  Time      // Johnson 势函数（用于 Dijkstra 重标号）
  depth:      Int       // 搜索深度（用于环路检测）
  predecessor: Dedge*   // 前驱边（用于回溯路径）
  generation: Int       // 搜索代（用于判断是否已访问）
  inArray:  Dedge*[]    // 入边数组
  outArray: Dedge*[]    // 出边数组

结构体 Dedge:
  from:   Dnode&        // 起点
  to:     Dnode&        // 终点
  length: Time          // 边权（当前最紧约束）
  lengthSpecs: Time[]   // 所有约束规格（可能有多条约束共享同一边）

结构体 BucketQueue:
  // 桶排序优先队列，用于 Dijkstra
  // 键值 = distance - potential（Johnson 重标号后的非负权重）
  insertInQueue(node, key)
  popMinFromQueue() → node
```

---

## 3. 约束添加与边创建

当 EUROPA 添加一条时序约束 `lb ≤ targ - src ≤ ub` 时：

```
算法: ADD_TEMPORAL_CONSTRAINT(src, targ, lb, ub)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  // 1. 编码为距离图的边
  IF ub ≤ MAX_LENGTH:
    ADD_EDGE_SPEC(src, targ, ub)     // 上界边: src → targ, 权重 ub
  IF lb ≥ MIN_LENGTH:
    ADD_EDGE_SPEC(targ, src, -lb)    // 下界边: targ → src, 权重 -lb

  // 2. 增量传播
  INC_PROPAGATE(src, targ)
```

```
算法: ADD_EDGE_SPEC(from, to, length)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  edge ← FIND_EDGE(from, to)
  IF edge = null:
    edge ← CREATE_EDGE(from, to, length)
  edge.lengthSpecs.APPEND(length)
  // 边权取所有规格的最小值（最紧约束）
  IF length < edge.length:
    edge.length ← length
```

**JxbMove 示例**: `eq(duration, 523)` 即 `MoveToOn900Base2.start + 523 = MoveToOn900Base2.end`

编码为：
- `start → end`，权重 523（end - start ≤ 523）
- `end → start`，权重 -523（end - start ≥ 523）

即：`end - start = 523`

---

## 4. 增量传播算法 (incPropagate)

这是核心算法，当添加一条新约束后被调用。它包含三个阶段：

```
算法: INC_PROPAGATE(src, targ)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  IF 有待处理的删除 OR 已不一致:
    RETURN    // 需要完全重传播

  // ──── 阶段 1: 一致性检查 (增量 Bellman-Ford) ────
  next ← START_NODE(src, src.potential, targ, targ.potential, forward=true)
  IF next ≠ null:
    // 检测新边是否引入负环（不一致）
    consistent ← INC_BELLMAN_FORD()
    IF NOT consistent:
      RETURN    // 检测到不一致！

  // ──── 阶段 2: 上界传播 (增量 Dijkstra 前向) ────
  next ← START_NODE(src, src.upperBound, targ, targ.upperBound, forward=true)
  IF next ≠ null:
    queue.INSERT(next)
    INC_DIJKSTRA_FORWARD()    // 传播上界收紧

  // ──── 阶段 3: 下界传播 (增量 Dijkstra 后向) ────
  // 注意: 下界用负值编码，所以是反向传播
  headDist ← -(src.lowerBound)
  footDist ← -(targ.lowerBound)
  next ← START_NODE(src, headDist, targ, footDist, forward=false)
  IF next ≠ null:
    src.lowerBound ← -headDist
    targ.lowerBound ← -footDist
    queue.INSERT(next)
    INC_DIJKSTRA_BACKWARD()   // 传播下界收紧
```

### 4.1 START_NODE — 第一步传播

```
算法: START_NODE(head, headDistance, foot, footDistance, forwards)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  // 检查正向边 head → foot 是否能改进 foot 的距离
  edge ← FIND_EDGE(head → foot)    // 如果是反向则 foot → head
  IF edge ≠ null AND headDistance < +∞
     AND headDistance + edge.length < footDistance:
    footDistance ← headDistance + edge.length
    head.depth ← 0
    foot.depth ← 1
    RETURN foot    // 从 foot 继续传播

  // 检查反向边 foot → head 是否能改进 head 的距离
  revEdge ← FIND_EDGE(foot → head)
  IF revEdge ≠ null AND footDistance < +∞
     AND footDistance + revEdge.length < headDistance:
    headDistance ← footDistance + revEdge.length
    foot.depth ← 0
    head.depth ← 1
    RETURN head    // 从 head 继续传播

  RETURN null    // 新边不影响任何距离
```

**关键洞察**: 如果新边不能改进任何端点的距离，则无需传播。这是增量算法的效率来源。

### 4.2 增量 Dijkstra 前向 — 传播上界

```
算法: INC_DIJKSTRA_FORWARD()
━━━━━━━━━━━━━━━━━━━━━━━━━━━

  // 从原点出发，沿正向边传播上界
  // 使用 Johnson 重标号: key = upperBound - potential
  //   确保所有边权非负，可以用 Dijkstra

  WHILE true:
    node ← queue.POP_MIN()
    IF node = null:
      RETURN

    FOR EACH edge IN node.outArray:
      next ← edge.to
      newDistance ← node.upperBound + edge.length

      IF newDistance < next.upperBound:
        // 发现更紧的上界！
        ASSERT(next.depth = node.depth + 1) ≤ N    // 环路检测
        next.upperBound ← newDistance
        // Johnson 重标号: 非负键值
        queue.INSERT(next, key = newDistance - next.potential)
        MARK_UPDATED(next)
```

**为什么用 Dijkstra 而不是 Bellman-Ford？**

距离图的边权可以为负（如 `-lb` 边），传统 Dijkstra 无法处理负权边。EUROPA 使用 **Johnson 重标号技术**：

1. 先用 Bellman-Ford 计算每个节点的势函数 `potential`
2. 将边权重标号为 `w'(u,v) = w(u,v) + potential(u) - potential(v)` ≥ 0
3. 用 Dijkstra 在重标号后的非负权图上传播
4. 最终距离 = Dijkstra距离 + potential

因为势函数在完全传播后已经计算好，增量添加一条边时只需局部传播，用 Dijkstra 的 O((V+E) log V) 代替 Bellman-Ford 的 O(VE)。

### 4.3 增量 Dijkstra 后向 — 传播下界

```
算法: INC_DIJKSTRA_BACKWARD()
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  // 下界传播: 计算 -(lowerBound) 沿反向边的最短路径
  // 即: 从当前节点出发，沿入边反向传播

  WHILE true:
    node ← queue.POP_MIN()
    IF node = null:
      RETURN

    FOR EACH edge IN node.inArray:          // 注意: 遍历入边！
      next ← edge.from                      // 注意: 是 from，不是 to！
      newDistance ← -(node.lowerBound) + edge.length

      IF newDistance < -(next.lowerBound):
        // 发现更紧的下界！
        next.lowerBound ← -newDistance       // 取负还原
        ASSERT(next.depth = node.depth + 1) ≤ N
        queue.INSERT(next, key = newDistance + next.potential)
        MARK_UPDATED(next)
```

**为什么是反向？**

`lowerBound(T)` = -(从 T 到原点 O 的最短路径)。添加边 A→B(ub) 后，如果 B 的下界变了，可能影响 B 的所有前驱节点的下界。因此沿入边反向传播。

---

## 5. 完全重传播 (fullPropagate)

当有约束被删除时，增量传播不再有效（删除可能使之前不可能的路径变为可能），需要从头计算。

```
算法: FULL_PROPAGATE()
━━━━━━━━━━━━━━━━━━━━━

  // 1. Bellman-Ford 计算势函数并检测一致性
  consistent ← BELLMAN_FORD()
  IF NOT consistent:
    RETURN

  // 2. 初始化所有节点界
  FOR EACH node IN nodes:
    node.upperBound ← +∞
    node.lowerBound ← -∞

  // 3. 从原点开始传播
  origin.upperBound ← 0
  origin.lowerBound ← 0

  // 4. 前向 Dijkstra: 计算所有上界
  queue.INSERT(origin)
  INC_DIJKSTRA_FORWARD()

  // 5. 后向 Dijkstra: 计算所有下界
  queue.INSERT(origin)
  INC_DIJKSTRA_BACKWARD()
```

---

## 6. Bellman-Ford 一致性检测

```
算法: BELLMAN_FORD()
━━━━━━━━━━━━━━━━━━━

  // 计算所有节点的势函数（最短路径距离）
  // 同时检测负环（不一致）

  FOR EACH node IN nodes:
    node.distance ← node.potential    // 使用上次的势作为初始值
    node.potential ← 0
    node.depth ← 0
    queue.INSERT(node, key = -oldPotential)

  BFbound ← |nodes|    // 最大松弛次数

  WHILE true:
    node ← queue.POP_MIN()
    IF node = null:
      BREAK

    FOR EACH edge IN node.outArray:
      next ← edge.to
      potential ← node.potential + edge.length

      IF potential < next.potential:
        next.potential ← potential
        next.predecessor ← edge

        // ── 环路检测 ──
        IF next.depth = node.depth + 1 > BFbound:
          // 深度超过节点数 → 存在负环 → 不一致!
          RETURN false

        IF CYCLE_DETECTED(next):
          // 跟踪前驱边回溯到负环
          RETURN false

        queue.INSERT(next, key = potential - oldPotential)

  RETURN true    // 一致
```

**增量 Bellman-Ford (`incBellmanFord`)**: 与完全版相同，但只从受影响的节点开始，并使用 `generation` 标记避免重复处理。

---

## 7. 双向同步: 约束引擎 ↔ STN

```
算法: TemporalPropagator.EXECUTE()
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  // 1. CE → STN: 将约束引擎的变化应用到时序网络
  UPDATE_TNET()
    // 处理约束删除 → 标记 hasDeletions
    // 处理变量删除 → 移除时间点
    // 处理变量域变化 → 调用 NARROW_TEMPORAL_CONSTRAINT
    // 处理新约束 → 调用 ADD_TEMPORAL_CONSTRAINT

  // 2. STN 内部传播
  consistent ← STN.PROPAGATE()

  // 3. STN → CE: 将传播后的界推回约束引擎
  IF consistent:
    UPDATE_CNET()
```

```
算法: UPDATE_CNET()    // STN 界 → CE 变量域
━━━━━━━━━━━━━━━━━━━━━

  FOR EACH timepoint IN stn.updatedTimepoints:
    var ← TIMEPOINT_TO_VARIABLE(timepoint)
    lb ← timepoint.lowerBound
    ub ← timepoint.upperBound

    domain ← var.currentDomain    // IntervalIntDomain
    IF lb ≠ domain.lb OR ub ≠ domain.ub:
      domain.INTERSECT(lb, ub)    // 收窄 CE 中的变量域
      // → 触发 CE 的进一步传播（非时序约束）
```

```
算法: ADD_TIMEPOINT(var)    // CE 变量 → STN 时间点
━━━━━━━━━━━━━━━━━━━━━━━━━

  tp ← STN.ADD_TIMEPOINT()
  MAP(var ↔ tp)

  // 创建基础域约束: origin 到 tp 的距离在 [lb, ub] 之间
  lb ← var.domain.lowerBound
  ub ← var.domain.upperBound
  STN.ADD_TEMPORAL_CONSTRAINT(origin, tp, lb, ub)
```

---

## 8. JxbMove 中的 STN 传播实例

以添加约束 `contained_by(MoveToBase2, comm2)` 为例，其中 `comm2 = InComms(690, 1200)`：

`contained_by` 展开为两个时序约束：
- `comm2.start ≤ MoveToBase2.start` 即 `MoveToBase2.start - comm2.start ≥ 0`
- `MoveToBase2.end ≤ comm2.end` 即 `comm2.end - MoveToBase2.end ≥ 0`

### 步骤 1: 添加约束前的 STN 状态

```
节点 (相对于 origin=0):
  comm2.start:  [690, 690]     (固定值)
  comm2.end:    [1200, 1200]   (固定值)
  MoveToBase2.start: [-∞, +∞]  (未约束)
  MoveToBase2.end:   [-∞, +∞]  (未约束)
  MoveToBase2.duration: [203, 203] (eq约束)
```

### 步骤 2: 添加 `MoveToBase2.start ≥ comm2.start`

即 `0 ≤ MoveToBase2.start - comm2.start`

编码: `comm2.start → MoveToBase2.start`，权重 +∞（无上界）
      `MoveToBase2.start → comm2.start`，权重 0（下界为0）

```
ADD_TEMPORAL_CONSTRAINT(comm2.start, MoveToBase2.start, 0, +∞)
  → ADD_EDGE_SPEC(MoveToBase2.start, comm2.start, 0)   // -lb = 0

INC_PROPAGATE:
  START_NODE: MoveToBase2.start.lb = -∞, comm2.start.lb = 690
    edge: MoveToBase2.start → comm2.start, length=0
    -(MoveToBase2.start.lb) + 0 = +∞ > -(comm2.start.lb) = -690? 不改进
    反向: comm2.start → MoveToBase2.start (不存在)
  → 无传播需要（因为 MoveToBase2.start 已经是 -∞）
```

### 步骤 3: 添加 `MoveToBase2.end ≤ comm2.end`

即 `0 ≤ comm2.end - MoveToBase2.end`

```
ADD_TEMPORAL_CONSTRAINT(MoveToBase2.end, comm2.end, 0, +∞)
  → ADD_EDGE_SPEC(comm2.end, MoveToBase2.end, 0)   // -lb = 0

INC_PROPAGATE:
  前向 START_NODE: comm2.end.ub=1200, MoveToBase2.end.ub=+∞
    edge: comm2.end → MoveToBase2.end, length=0
    1200 + 0 = 1200 < +∞ ✓ → footDistance 更新为 1200
  → MoveToBase2.end 入队

  INC_DIJKSTRA_FORWARD:
    弹出 MoveToBase2.end (upperBound=1200)
    遍历出边: MoveToBase2.end → MoveToBase2.start, length=-203 (duration约束)
      newDistance = 1200 + (-203) = 997
      997 < MoveToBase2.start.upperBound(+∞) → 更新!
      MoveToBase2.start.upperBound ← 997
      入队 MoveToBase2.start

    弹出 MoveToBase2.start (upperBound=997)
    遍历出边: MoveToBase2.start → comm2.start, length=0
      newDistance = 997 + 0 = 997
      997 > comm2.start.upperBound(690) → 不更新
    遍历出边: MoveToBase2.start → AtBase2的前驱 ...
      (类似传播)

  后向 INC_DIJKSTRA_BACKWARD:
    START_NODE: MoveToBase2.end.lb=-∞
      edge: MoveToBase2.start → MoveToBase2.end, length=203
      comm2.start → MoveToBase2.start (length=+∞? 无此边)
      ...
    → MoveToBase2.start.lowerBound ← 690 (从comm2.start传播)
    → MoveToBase2.end.lowerBound ← 690 + 203 = 893
```

### 步骤 4: 传播结果

```
MoveToBase2.start: [690, 997]
MoveToBase2.end:   [893, 1200]
duration:          [203, 203]
```

这与 EUROPA 实际输出一致！

---

## 9. 算法复杂度

| 操作 | 复杂度 | 说明 |
|------|--------|------|
| 添加一条约束 | O((V+E) log V) | 增量 Dijkstra，V=时间点数, E=边数 |
| 删除一条约束 | O(VE) | 需要完全重传播 (Bellman-Ford + Dijkstra) |
| 完全传播 | O(VE + (V+E) log V) | Bellman-Ford + 两次 Dijkstra |
| 查询时间点界 | O(1) | 直接读取 lowerBound/upperBound |
| 一致性检查 | O(1) | 传播时已检测 |

**JxbMove 实际规模**: ~40 个时间点、~80 条边。每次增量传播在微秒级完成。

---

## 10. 与标准 Dijkstra 的关键区别

| 特性 | 标准 Dijkstra | EUROPA STN Dijkstra |
|------|--------------|---------------------|
| 边权 | 非负 | 可为负（通过 Johnson 重标号处理） |
| 源点 | 单源 | 增量：仅从受影响节点开始 |
| 方向 | 单向（前向） | 双向：前向传播上界、后向传播下界 |
| 终止 | 到达目标即停 | 传播到所有受影响节点（不动点） |
| 一致性 | 不检测 | 通过深度限制和环路检测（Bellman-Ford）|
| 优先队列 | 二叉堆 | 桶排序队列（利用整数权重，O(1) 插入/弹出）|
| 增量性 | 无 | `startNode()` 跳过无影响的边 |
