# EUROPA 工作原理总结

## 1. 概述

EUROPA（Extensible Universal Remote Operations Planning Architecture）是由 NASA Ames 研究中心开发的开源规划与调度框架。它用于解决**自动规划（Planning）**、**调度（Scheduling）**和**约束编程（Constraint Programming）**问题，广泛应用于火星探测器任务规划、空间站资源管理等 NASA 任务。

EUROPA 的核心理念是：将一个不完整的**部分计划（Partial Plan）**逐步精化为一个**完整计划（Complete Plan）**，通过不断发现并修复计划中的**缺陷（Flaw）**来实现这一过程。

---

## 2. 系统架构

EUROPA 由以下核心模块组成，按照依赖关系自底向上排列：

```
┌─────────────────────────────────────────────────────┐
│                    System / PSEngine                  │  ← 对外公共 API
├─────────────────────────────────────────────────────┤
│     Solvers          │        Resource               │  ← 搜索引擎 / 资源管理
├─────────────────────────────────────────────────────┤
│     NDDL             │        ANML                   │  ← 建模语言解析
├──────────────────────┼──────────────────────────────┤
│  TemporalNetwork     │     RulesEngine               │  ← 时序推理 / 规则引擎
├─────────────────────────────────────────────────────┤
│                  PlanDatabase                         │  ← 计划数据库
├─────────────────────────────────────────────────────┤
│                ConstraintEngine                       │  ← 约束传播引擎
├─────────────────────────────────────────────────────┤
│          Utils / TinyXml                             │  ← 基础工具
└─────────────────────────────────────────────────────┘
```

### 2.1 基础层（Utils）

提供整个系统的基础设施：

- **Entity** — 所有系统实体的基类，提供引用计数和全局注册表
- **Id\<T\>** — 带安全检查的智能指针，可检测悬空指针
- **LabelStr** — 字符串驻留（Interning）机制，将字符串编码为浮点数键以提高效率

### 2.2 约束引擎（ConstraintEngine）

EUROPA 的技术核心。它维护变量和约束的网络，通过**约束传播（Constraint Propagation）**自动收窄变量的可能取值范围。

**核心概念：**

| 概念 | 说明 |
|------|------|
| **Domain（域）** | 变量的取值空间。可以是区间（IntervalDomain）或枚举（EnumeratedDomain）。支持交集、差集、等化等操作 |
| **Variable（变量）** | 包含一个基础域（初始约束）和一个派生域（传播后的结果）。当派生域被收窄为单值时，变量被"确定" |
| **Constraint（约束）** | 变量之间的关系。当相关变量的域发生变化时，约束被唤醒并执行传播逻辑 |
| **Propagator（传播器）** | 管理一组约束的执行顺序。基于议程（Agenda）驱动，优先级排序 |

**工作方式：**

```
变量域变化 → 触发 DomainListener → 将相关约束加入传播器议程
→ 传播器按优先级执行约束 → 约束收窄变量域 → 可能触发更多变化
→ 重复直到到达不动点（一致性）或检测到矛盾（不一致性）
```

约束引擎有三种状态：
- `PENDING` — 存在待传播的变化
- `CONSTRAINT_CONSISTENT` — 所有约束已满足
- `PROVEN_INCONSISTENT` — 检测到矛盾，无解

### 2.3 计划数据库（PlanDatabase）

管理规划问题的核心数据结构：对象、令牌和全局变量。

**核心概念：**

| 概念 | 说明 |
|------|------|
| **Object（对象）** | 问题域中的实体（如 Rover、Battery）。包含成员变量，可以有层级关系 |
| **Token（令牌）** | 表示一个**动作（Action）**或**状态（State）**在时间轴上的存在。每个 Token 自带 start、end、duration、state 等变量 |
| **Timeline（时间线）** | 一种特殊的 Object，强制其上的 Token 形成有序序列（不允许重叠） |

**Token 生命周期：**

```
INCOMPLETE → INACTIVE → ACTIVE（占据时间线位置）
                     → MERGED（与已有 Token 合并）
                     → REJECTED（排除此可能性）
```

- **Fact** — 确定发生的事实（如 "Rover 在时刻 0 位于 Lander"）
- **Goal** — 需要达成的目标（如 "在 Rock4 采集样本"）
- **Master/Slave** — Token 之间的因果关系：Master Token 通过规则生成 Slave Token

### 2.4 规则引擎（RulesEngine）

实现**动作分解**和**因果推理**。当一个 Token 被激活时，与之关联的规则自动触发，生成子目标（Slave Token）和约束。

**工作方式：**

```
Token 被激活 → 查找该谓词的所有规则 → 创建 RuleInstance
→ 检查守卫变量 → 满足条件时执行规则
→ 创建 Slave Token（子目标）+ 新约束
```

例如，当 `Rover::Go` 动作被激活时：
1. 创建 `Navigator.At` 的前置条件（`met_by`）和后置效果（`meets`）
2. 创建 `Battery.consume` 事务
3. 添加路径约束
4. 要求仪器处于收起状态（`contained_by`）

### 2.5 时序网络（TemporalNetwork）

实现**简单时序网络（Simple Temporal Network, STN）**算法。

- 维护时间点之间的距离约束（上下界）
- 基于 Dijkstra 的增量传播算法
- 与约束引擎双向同步：约束引擎中的时序变量变化 ↔ 时序网络中的时间点约束
- 支持查询：`canPrecede()`（是否能在之前）、`canFitBetween()`（是否能嵌入两时间点之间）

**支持的时序关系：**

| 关系 | 语义 |
|------|------|
| `meets(A, B)` | A 结束时刻 = B 开始时刻 |
| `met_by(A, B)` | B 结束时刻 = A 开始时刻 |
| `before(A, B)` | A 在 B 之前 |
| `contains(A, B)` | A 包含 B |
| `contained_by(A, B)` | A 被 B 包含 |
| `equals(A, B)` | A 和 B 时间完全相同 |
| `starts(A, B)` | A 和 B 同时开始 |

### 2.6 求解器（Solvers）

EUROPA 的搜索引擎，采用**时序回溯搜索（Chronological Backtracking Search）**策略。

**核心组件：**

| 组件 | 说明 |
|------|------|
| **Solver** | 搜索协调器，管理决策栈和缺陷管理器 |
| **FlawManager** | 缺陷收集器，按优先级维护待解决的缺陷 |
| **FlawHandler** | 决策点工厂，为每种缺陷类型创建解决方案 |
| **DecisionPoint** | 一个具体的决策，包含多个可选方案 |

**四类缺陷（Flaw）：**

1. **OpenCondition（开放条件）** — 未被解决的子目标 Token。解决方式：激活、合并到已有 Token、或拒绝
2. **Threat（威胁）** — 时间线上 Token 的排序冲突。解决方式：确定 Token 顺序
3. **UnboundVariable（未绑定变量）** — 需要赋值的变量。解决方式：从域中选择一个值
4. **ResourceThreat（资源威胁）** — 资源使用冲突（超限）。解决方式：调整 Token 时序

**求解流程：**

```
while (存在缺陷) {
    1. 从 FlawManager 获取最高优先级缺陷
    2. 创建 DecisionPoint
    3. 选择第一个可选方案，应用到计划中
    4. 触发约束传播
    5. if (不一致) {
         回溯：撤销决策，尝试下一个方案
         if (方案耗尽) 继续回溯到上一个决策
       }
    6. 将决策压入决策栈
}
```

### 2.7 资源管理（Resource）

EUROPA 提供三种资源模型：

| 资源类型 | 说明 | 典型应用 |
|---------|------|---------|
| **Reservoir** | 可消耗/可生产的资源，单事务 | 电池电量、燃料 |
| **Reusable** | 可复用的资源，获取/释放两事务 | 工具、通信信道 |
| **Unary** | 容量为 1 的 Reusable，独占使用 | 钻头、机械臂 |

每种资源维护**配置文件（Profile）**来追踪资源水平随时间的变化，并检测违规：
- `LevelTooHigh` — 超出上限
- `LevelTooLow` — 低于下限
- `ProductionRateExceeded` — 生产速率超限
- `ConsumptionRateExceeded` — 消耗速率超限

---

## 3. NDDL 建模语言

NDDL（New Domain Definition Language）是 EUROPA 的声明式建模语言，用于定义问题域和初始状态。

### 3.1 类定义

```nddl
class Rover {
    Navigator navigator;
    Battery mainBattery;

    Rover(Battery b) {
        navigator = new Navigator();
        mainBattery = b;
    }

    action Go { Location dest; }
    action TakeSample { Location rock; }
}
```

- 支持继承（`extends`）
- 内建类型：`Timeline`（有序时间线）、`Reservoir`（水库资源）、`Reusable`（可复用资源）
- `action` 定义可执行的动作
- `predicate` 定义可存在的状态

### 3.2 规则定义（动作体）

```nddl
Rover::Go {
    // 前置条件：Rover 当前位于 _from 位置
    met_by(condition object.navigator.At _from);
    // 后置效果：Rover 到达 dest 位置
    meets(effect object.navigator.At _to);
    eq(_to.location, dest);

    // 仪器必须在行驶时收起
    contained_by(condition object.instrument.location.Stowed);

    // 消耗电池电量
    starts(effect object.mainBattery.consume tx);
    eq(tx.quantity, path.cost);
}
```

- `condition` — 前置条件（必须已存在的状态）
- `effect` — 后置效果（动作产生的结果）
- `met_by` / `meets` — 时序关系（紧接前/后）
- `eq` / `neq` — 等式/不等式约束

### 3.3 问题实例

```nddl
#include "Rover-model.nddl"

// 创建对象
Location lander = new Location("LANDER", 0, 0);
Location rock4 = new Location("ROCK4", 3, 9);
Path p1 = new Path("Short Cut", lander, rock4, 400.0);
Battery battery = new Battery(1000.0, 0.0, 1000.0);
Rover spirit = new Rover(battery);
close();  // 关闭数据库，不再创建新对象

// 初始事实
fact(spirit.navigator.At initialPosition);
eq(initialPosition.start, 0);
eq(initialPosition.location, lander);

// 规划目标
goal(spirit.TakeSample sample);
sample.rock.specify(rock4);
```

---

## 4. 端到端工作流程

以 Rover 采样任务为例，展示 EUROPA 完整的求解过程：

### 第 1 步：模型加载

```
NDDL 文件 → ANTLR3 解析器 → Schema 注册 → Plan Database 初始化
```

系统解析 NDDL 文件，注册类型定义、谓词和规则到 Schema 中。

### 第 2 步：问题实例化

```
创建对象（Rover, Battery, Location, Path）
→ 创建 Fact Token（初始状态）
→ 创建 Goal Token（目标）
→ 关闭数据库
```

此时计划数据库中存在多个**缺陷**：
- Goal Token `TakeSample` 是一个 OpenCondition
- 目标的 start/end 等变量尚未绑定

### 第 3 步：求解循环

```
迭代 1: 发现缺陷 → TakeSample 是 OpenCondition
        决策 → 激活 TakeSample Token
        规则触发 → 创建子目标:
          - Navigator.At (条件: Rover 在 rock4)
          - Instrument.TakeSample (子任务)
          - PhoneHome 或 PhoneLander (通信)
        约束传播 → 收窄时间变量

迭代 2: 发现缺陷 → Instrument.TakeSample 是 OpenCondition
        决策 → 激活，触发更多子目标:
          - Instrument.Placed (条件)
          - Instrument.Sampling (效果)
          - Battery.consume (资源消耗)

迭代 3: 发现缺陷 → Navigator.At 是 OpenCondition
        决策 → 需要 Go 动作将 Rover 移动到 rock4
        规则触发 → 创建:
          - Navigator.At 前置 (在 lander)
          - Navigator.Going (行进中)
          - Battery.consume (路径成本)
          - Instrument.Stowed (约束)

... 持续迭代 ...

迭代 N: 发现缺陷 → Threat (时间线排序)
        决策 → 确定 Token 顺序

迭代 N+1: 发现缺陷 → 资源违规 (电池电量不足)
          回溯 → 选择成本更低的路径 (Short Cut: 400)

迭代 M: 无更多缺陷 → 求解成功！
```

### 第 4 步：结果

最终生成一个完整的计划：

```
t=0:  Rover 在 Lander, 仪器收起, 电池=1000
t=1:  Unstow 仪器 (消耗 20)
t=3:  Stow 仪器 (消耗 20)
t=5:  Go Lander→Rock4 via ShortCut (消耗 400)
t=15: Unstow 仪器 (消耗 20)
t=17: Place 仪器 (消耗 20)
t=20: TakeSample at Rock4 (消耗 120)
t=50: PhoneLander (消耗 20) ← 选择低成本的通信方式
      电池剩余 = 1000 - 400 - 20*4 - 120 - 20 = 380
```

---

## 5. 求解器配置

通过 XML 文件控制求解行为：

```xml
<Solver name="DefaultTestSolver">
  <!-- 全局过滤：只处理时间范围内的 Token -->
  <FlawFilter component="HorizonFilter" policy="PartiallyContained"/>

  <!-- 资源威胁管理器 -->
  <ResourceThreatManager defaultPriority="0">
    <FlawHandler class-match="Reservoir" component="ResourceThreatHandler"/>
    <FlawHandler class-match="Reusable"  component="ResourceThreatHandler"/>
  </ResourceThreatManager>

  <!-- 时序威胁管理器 -->
  <ThreatManager defaultPriority="0">
    <FlawHandler component="StandardThreatHandler"/>
  </ThreatManager>

  <!-- 开放条件管理器 -->
  <OpenConditionManager defaultPriority="0">
    <FlawHandler component="StandardOpenConditionHandler"/>
  </OpenConditionManager>

  <!-- 未绑定变量管理器 -->
  <UnboundVariableManager defaultPriority="0">
    <FlawFilter var-match="start"/>   <!-- 排除时序变量 -->
    <FlawFilter var-match="end"/>
    <FlawFilter var-match="duration"/>
    <FlawHandler component="StandardVariableHandler"/>
  </UnboundVariableManager>
</Solver>
```

**配置要点：**
- `defaultPriority` — 缺陷管理器的优先级，影响求解顺序
- `FlawFilter` — 排除特定变量或类型的缺陷
- `FlawHandler` — 为特定类型的缺陷指定处理策略
- `class-match` — 按类型名称匹配
- `component` — 使用的处理器实现

---

## 6. 扩展机制

EUROPA 的模块化设计提供多个扩展点：

| 扩展点 | 基类 | 用途 |
|--------|------|------|
| 自定义约束 | `Constraint` | 定义新的约束类型 |
| 自定义传播器 | `Propagator` | 定义新的传播策略 |
| 自定义缺陷处理 | `FlawHandler` | 定义新的缺陷解决策略 |
| 自定义资源 | `Resource` | 定义新的资源类型 |
| 自定义规则 | `Rule` | 定义新的规则逻辑 |

---

## 7. PSEngine 公共 API

PSEngine 是 EUROPA 的对外接口，支持 C++ 和 Java（通过 SWIG 绑定）：

```cpp
// 创建并启动引擎
PSEngine* engine = PSEngine::makeInstance();
engine->start();

// 加载 NDDL 模型
engine->executeScript("nddl", "model.nddl", true);

// 查询计划数据库
PSList<PSObject*> objects = engine->getObjects();
PSList<PSToken*> tokens = engine->getTokens();

// 创建并运行求解器
PSSolver* solver = engine->createSolver("PlannerConfig.xml");
solver->configure(0, 1000);   // 设置时间范围
solver->solve(1000, 1000);    // 最多 1000 步，最大深度 1000

// 检查结果
if (solver->isExhausted()) { /* 无解 */ }
if (solver->isTimedOut())  { /* 超时 */ }
if (solver->getFlaws() == 0) { /* 求解成功 */ }

// 清理
solver->reset();
engine->shutdown();
```

---

## 8. 设计模式总结

| 模式 | 应用 |
|------|------|
| **观察者（Observer）** | DomainListener、PlanDatabaseListener、SearchListener |
| **工厂（Factory）** | FlawHandler 创建 DecisionPoint、Constraint 注册 |
| **中介者（Mediator）** | ConstraintEngine 协调变量和约束、Solver 协调 FlawManager |
| **命令（Command）** | Constraint 的 handleExecute()、DecisionPoint 的 execute/undo |
| **模板方法（Template Method）** | Propagator 的传播算法、FlawManager 的缺陷遍历 |
| **策略（Strategy）** | 不同的 FlawHandler 实现、不同的 Profile 类型 |

---

## 9. 项目结构

```
europa/
├── src/
│   ├── PLASMA/                    # C++ 核心
│   │   ├── Utils/                 # 基础工具
│   │   ├── TinyXml/               # XML 解析
│   │   ├── ConstraintEngine/      # 约束引擎
│   │   ├── PlanDatabase/          # 计划数据库
│   │   ├── RulesEngine/           # 规则引擎
│   │   ├── TemporalNetwork/       # 时序网络
│   │   ├── NDDL/                  # NDDL 语言解析器
│   │   ├── Solvers/               # 求解器
│   │   ├── Resource/              # 资源管理
│   │   ├── ANML/                  # ANML 语言支持
│   │   └── System/                # PSEngine 集成层
│   └── Java/                      # Java 绑定和 UI
│       ├── PSEngine/              # SWIG Java 接口
│       └── JavaUI/                # Swing 可视化工具
├── examples/                      # 示例项目
│   ├── Rover/                     # 火星探测器规划
│   ├── Light/                     # 灯泡开关（入门示例）
│   ├── Shopping/                  # 购物规划
│   ├── BlocksWorld/               # 积木世界
│   ├── NQueens/                   # N 皇后问题
│   └── UBO/                       # 资源约束项目调度
├── config/                        # 运行时配置
│   ├── PlannerConfig.xml          # 求解器配置
│   ├── NDDL.cfg                   # NDDL 类型绑定
│   └── Debug.cfg                  # 调试开关
├── ext/lib/                       # 外部依赖
│   └── antlr-3.jar                # ANTLR3 解析器生成器
├── build.xml                      # Ant 构建文件
└── CMakeLists.txt                 # CMake 构建文件
```

---

## 10. 总结

EUROPA 是一个强大的 AI 规划框架，其核心工作机制可以用一句话概括：

> **从一个不完整的部分计划出发，通过约束传播维护一致性，通过缺陷检测发现问题，通过搜索和回溯寻找解决方案，最终生成一个满足所有时序约束和资源限制的完整计划。**

其关键创新在于：
1. **统一表示** — 规划和调度问题在同一框架下处理
2. **约束驱动** — 通过约束传播实现高效的推理和剪枝
3. **声明式建模** — NDDL 语言让用户专注于"是什么"而非"怎么做"
4. **可扩展架构** — 模块化设计允许自定义约束、资源类型和求解策略
