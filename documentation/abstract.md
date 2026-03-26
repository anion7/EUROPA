# 摘要

针对空间站机械臂在轨操作中通信窗口受限与机械臂遮挡约束耦合导致任务规划困难的问题，提出一种基于时空解耦策略的任务规划方法。该方法将连续运动过程与离散任务调度相分离：利用SGP4轨道传播模型与DH运动学正解联合确定通信可见窗口和遮挡约束区间；基于梯形速度曲线解析公式预计算各移动段持续时间，将连续动力学转化为固定时长的调度问题；采用EUROPA规划框架的缺陷导向时序回溯搜索算法求解，通过简单时序网络的增量Dijkstra传播实现高效约束推理。以包含六个阶段二十三项子任务的机械臂全流程操作为算例，实验结果表明该方法在亚秒级时间内生成满足通信窗口和遮挡回避约束的可行计划，相比基于PDDL+的UPMurphi规划器在长时间跨度问题上具有显著效率优势，验证了时空解耦策略与约束传播机制在空间机械臂任务规划中的有效性。

**关键词：** 空间机械臂；任务规划；时空解耦；约束传播；简单时序网络；EUROPA

---

# Abstract

To address the difficulty in task planning for space station robotic arms where limited communication windows are coupled with arm-induced link-occlusion constraints, a spatiotemporal-decoupling-based planning method is proposed. The method separates continuous motion computation from discrete task scheduling: the SGP4 orbital propagation model and Denavit–Hartenberg forward kinematics are jointly used to determine communication visibility windows and occlusion constraint intervals; the duration of each movement segment is analytically pre-computed from a trapezoidal velocity profile, converting the continuous dynamics into a fixed-duration scheduling problem; the flaw-directed temporal backtracking search algorithm of the EUROPA planning framework is then adopted, where incremental Dijkstra propagation over a Simple Temporal Network enables efficient constraint reasoning. A case study comprising six phases and twenty-three sub-tasks of a complete robotic arm operation mission is conducted. Experimental results demonstrate that the proposed method generates a feasible plan satisfying both communication-window and occlusion-avoidance constraints in sub-second time, exhibiting significant efficiency advantages over the PDDL+-based UPMurphi planner for long-horizon scheduling problems, and validating the effectiveness of the spatiotemporal decoupling strategy combined with constraint propagation in space robotic arm task planning.

**Keywords:** space robotic arm; task planning; spatiotemporal decoupling; constraint propagation; Simple Temporal Network; EUROPA
