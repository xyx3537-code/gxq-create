# CLAUDE.md — 环境病毒宿主预测软件 GXQ_Create

> 这是给 Claude Code 的项目记忆文件。每次 Claude Code 在本目录启动时会自动读取，用于建立项目上下文。
> 维护者：徐懿暄（XYX），中国海洋大学海德学院 2023 级食品科学与工程
> 最后更新：2026-05-19（ORF 自动翻译模式恢复，双模式预测完整记录）

---

## 1. 项目身份与一句话目标

**项目名称**：环境病毒宿主预测软件的调研及开发（中国海洋大学 SRDP 校级一年期项目，批准经费 6500 元）

**一句话目标**：开发名为 **GXQ_Create** 的云端预测软件，基于自建多模态数据包 **XQ_Data**（D_1 基因组相似性 + D_2 蛋白质攻受结构），使用 SVM+Transformer 混合模型，预测环境病毒能感染哪些**真核**宿主（真菌、藻类、原生动物等），弥补现有工具几乎只能预测原核宿主/噬菌体—细菌的研究空白。

---

## 2. 核心创新（必须始终记住）

1. **聚焦真核宿主**——区别于 iPHoP、VirHostMatcher 等聚焦噬菌体-细菌的工具
2. **引入蛋白质攻受结合位点**——使用 ColabFold/HelixFold 预测三维结构 → 提取病毒表面蛋白 vs 宿主受体的结合位点
3. **多模态融合**——D_1（k-mer/CRISPR/tRNA/AMG 等序列特征）+ D_2（蛋白结构特征）→ 贝叶斯/加权平均融合
4. **混合模型架构**——SVM 处理 D_1 高维 k-mer，Transformer 处理 D_2 结构特征
5. **成型软件平台**——前端 React+D3，后端 Flask+Docker，云端 Kubernetes，弥补"只有算法没有工具"的空白

---

## 3. 团队与角色

| 角色 | 姓名 | 分工 |
|------|------|------|
| 项目负责人 | 徐懿暄（23220002070） | 数据分析、论文写作、软件、编码、可视化 |
| 项目组员 | 秦佳琳（23220002042） | 数据分析、论文、可视化、编码、财务 |
| 指导教师 | 汪岷（海德学院院长） | mingwang@ouc.edu.cn |
| 指导教师 | 高晨（助理教授） | gaochen@ouc.edu.cn |
| 指导教师 | 邵红兵（助理实验师） | hbshao@ouc.edu.cn |

团队拥有海洋宏组学/病毒组学多年积累，已发表 VITAP (Nature Communications 2025) 等多篇高水平论文，本项目可调用 INSDC、IMG/VR 等数据库与实验室高性能集群 + 公有云 GPU/TPU。

---

## 4. 当前真实进度（2026-05-15 复核）

⚠️ **重要**：申报书原始进度表已不准确。截至 2026-05-15，实际状态是：

- ✅ 申报书定稿（PDF 已解密保存）
- ⚠️ 文献综述：申报书声称"已完成"，但**实际只是初步试验，未形成可投稿的综述初稿**
- ✅ D_1 数据包 v1（基因组 k-mer 特征）：已完成原型
  - 数据：320 条真核病毒序列（fungi/algae/protozoa/bacteria 各 80）
  - 特征：3-mer 频率，64 维
  - 模型：SVM（RBF 核），5折交叉验证准确率 **94.1%**
  - 代码：scripts/00–03，data/processed/features.csv
- ✅ D_2 数据包 v1（蛋白质理化特征）：已完成原型
  - 数据：47,655 条蛋白质序列（来自同批 284 个病毒）
  - 特征：氨基酸组成 20维 + 理化性质 5维 + 蛋白数/均长 2维，共 27 维
  - 模型：SVM（RBF 核），5折交叉验证准确率 **94.0%**
  - 代码：scripts/04–06，data/processed/d2_features.csv
- ✅ XQ_Data 多模态融合 v1：已完成后期融合（late fusion）原型
  - 策略：0.6×D1概率 + 0.4×D2概率（最优权重网格搜索）
  - 融合后准确率 **95.4%**（较单模态提升 ~1.4%）
  - 代码：scripts/07_fuse_d1_d2.py，results/fusion_report.txt
- ✅ Flask API + Docker 容器化：已完成
  - 端点：POST /predict/sequence、POST /predict/fasta、GET /health
  - 镜像：gxq-create:v2（本地，用 `docker run -d -p 5000:5000 gxq-create:v2` 启动）
  - v2 已集成 ESM-2，模型预缓存进镜像，无需首次联网下载
  - 代码：app.py，Dockerfile，requirements.txt
- ✅ Streamlit 演示界面 v0.5：已完成（2026-05-19 最终版）
  - 功能：序列粘贴 / FASTA 上传；示例序列一键载入（NC_116874.1，9651 bp 完整基因组）
  - 支持 6 类宿主（fungi / algae / protozoa / bacteria / plant / invertebrate）
  - 可视化：环形气泡图（气泡大小=概率，顶部预测高亮，外侧标签完整显示）
  - 双模式预测（核心创新）：
    - DNA + 注释蛋白质：D1×0.4 + D2-ESM2×0.6，示例置信度 ~96.2%
    - 仅 DNA（创新）：自动翻译 6 阅读框 ORF → ESM-2 编码 → D1×0.7 + D2×0.3 融合
      示例置信度 ~70.8%；无需蛋白质注释，适合环境宏组学未知序列
      权重偏向 D1 是因为 ORF 扫描质量低于 NCBI 注释蛋白（可写入论文 Limitations）
  - 重要 bug 修复：GC 含量单位错误（小数 vs 百分比），修复前所有在线预测特征均错误
  - 启动：`conda activate virus && streamlit run streamlit_app.py`，访问 http://localhost:8501
  - 代码：streamlit_app.py（预测核心：scripts/09_predict.py）
- ✅ D_2 增强 v2（ESM-2 蛋白质语言模型 embedding）：已完成
  - 模型：facebook/esm2_t6_8M_UR50D（8M 参数，320 维 embedding，CPU 可运行）
  - 策略：每病毒最多 15 条蛋白，均值池化 → 320 维病毒向量
  - D2 ESM-2 单独准确率（原 4 类）：96.5%；扩充后 6 类：**95.5%**
  - 代码：scripts/10–11，data/processed/d2_esm2_features.csv，models/d2_esm2_pipeline.joblib
- ✅ XQ_Data 多模态融合 v2（D1 + D2-ESM2）：已完成
  - 最优权重：0.4×D1 + 0.6×D2-ESM2（网格搜索）
  - 融合后准确率（原 4 类）：96.8%；扩充后 6 类：**96.4%**
  - 代码：scripts/12_fuse_d1_esm2.py，results/fusion_esm2_report.txt
- ✅ 数据集扩充 v2（6 类，860 条）：已完成（2026-05-19）
  - 新增宿主类：plant（植物病毒）、invertebrate（无脊椎动物病毒）
  - 每类上限从 80 条提升至 150 条；protozoa 因 NCBI 库限制实际取 110 条
  - 蛋白质数据：81,380 条蛋白（860 个病毒）
  - D1 准确率（6 类）：**94.9%**；D2 ESM-2：**95.5%**；融合：**96.4%**
  - 注：准确率略低于原 4 类是因为 6 类问题本身更难，覆盖范围大幅扩展
- ✅ 在线预测验证（scripts/16_validate_online_predict.py）：已完成（2026-05-19）
  - 模式1（DNA + 注释蛋白质）：89.7%（61/68 条，仅含有注释蛋白的序列）
  - 模式2（仅 DNA，ORF 自动翻译，≥5000 bp 序列）：**90.9%**（80/88 条）
    - 各类：algae 14/15，bacteria 13/15，fungi 13/13，invertebrate 12/15，plant 15/15，protozoa 13/15
  - 关键发现：短序列（< 5000 bp）预测不可靠；藻类数据集中约 19% 为 ~1200–1800 bp 短序列，
    k-mer 统计不足，ORF 扫描仅得 1 条，ESM-2 特征退化为单蛋白 → 预测随机
  - 处置：在 09_predict.py 和 Streamlit UI 中加入短序列警告（`short_genome` 字段，阈值 5000 bp）
  - 网格搜索结论：ORF 模式最优 D1 权重为 0.6（与当前 0.7 准确率相同，略提升 D2 参与度）
- 已探索 D_1 增强（k-mer 扩展）：结论无提升
  - 尝试 1+2+3+4-mer 组合（344 维），准确率反降至 93.8%（原版 94.1%）
  - 根因：维度灾难，3-mer 是当前数据量下的最优 k 阶
  - 代码：scripts/13–15
  - 待办：CRISPR spacer / tRNA 特征（需外部数据库，单独规划）
- 未启动 SVM/Transformer 混合模型（完整版）
- 未启动 GXQ_Create 软件前端（React + D3）
- 未启动 湿实验验证

**当前已完成**：6 类数据集（860 条）；D1+D2-ESM2 融合 96.4%；Docker v2；Streamlit v0.5；在线验证（90.9% ORF 模式）；短序列警告
**当前最优模型**：D1（3-mer）+ D2-ESM2 融合，6 类，训练集交叉验证 **96.4%**，在线测试（≥5000 bp）**90.9%**
**下一步**：文献综述（实验结果已可写入 Methods）；或 CRISPR/tRNA 特征；或扩大数据集

---

## 5. 技术路线（按申报书）

```
病毒/宿主基因组   病毒-宿主蛋白
       │              │
       ▼              ▼
   k-mer/CRISPR    ColabFold/HelixFold
   tRNA/AMG          ↓
       │         三维结构 + 攻受位点
       ▼              │
     D_1 数据包       ▼
       │           D_2 数据包
       └──────┬───────┘
              ▼
        XQ_Data（贝叶斯/加权融合）
              │
       ┌──────┴───────┐
       ▼              ▼
     SVM        Transformer
       └──────┬───────┘
              ▼
       融合输出（感染概率 + 置信阈值）
              │
              ▼
    GXQ_Create（Flask + Docker + React + 云）
              │
              ▼
       干湿结合验证 → 数据回流 → 迭代
```

---

## 6. 同类工具调研清单

需在文献综述中深入对比：

| 工具 | 关键特点 | 局限 |
|------|---------|------|
| iPHoP | CRISPR spacer + k-mer + 同源 | 噬菌体-细菌 |
| CrisprOpenDB | 1100 万 spacers | 仅 CRISPR |
| PHIST | 精确匹配 | 仅原核 |
| HostPhinder | 噬菌体基因组相似性 | 不适用其他病毒 |
| HostNet | K2V 表示学习 + 1377 病毒 | 数据集偏窄 |
| VIDHOP | 双向 LSTM + CNN | 序列层面 |
| BLAST | 序列相似性 | 通用工具，非专用 |
| RNAVirHost | 基因组 + 同源 + ML | RNA 为主 |
| VirHostMatcher | 宏病毒组匹配 | 灵敏但仍偏原核 |

---

## 7. 经费预算（10000 元总预算，校拨 6500 元）

- 计算/分析/测试费：3500 元
- 论文出版费：2500 元
- 实验装置（DNA 提取试剂盒 + 测序）：2500 元
- 材料费：500 元

---

## 8. 用户协作偏好（请 Claude Code 遵守）

- 用户是**生信跨界初学者**（食品科学背景），Python/命令行/Linux 工具使用为新手
- 每引入新概念/新命令时先用一两句话解释"是什么"
- 操作步骤分点编号，每步可独立完成
- 输出代码或命令时附中文注释
- 避免一次性堆术语；术语首次出现给中文释义
- **但**：用户在科研写作上已有经验（曾以共同一作发 SCI Q1 Green Chemistry, IF 9.3），文献综述类内容可以技术深度较高

---

## 9. 工作目录与环境

- **Windows 端项目目录**（Cowork 桌面应用使用）：`D:\onedrive\OneDrive - Adelaide University\Documents\Claude\Projects\VIRUS-HOST\`
- **WSL/Linux 代码目录**（Claude Code CLI 使用）：`~/projects/virus_project/`
- **Python 环境**：conda 虚拟环境 `virus`（已激活时终端前缀显示 `(virus)`）
- **Claude Code 版本**：v2.1.133（Claude Pro 账户）

---

## 10. 下一步阶段任务（截至 2026-05）

**阶段 0：文献调研与综述（当前阶段）**

1. 系统检索近 5 年环境病毒宿主预测相关文献（PubMed/Web of Science/Google Scholar）
2. 深入测评 9 个同类工具（运行/对比/优劣）
3. 调研蛋白质三维结构预测方法（AlphaFold2、ColabFold、HelixFold、ESMFold）
4. 调研深度学习在病毒-宿主互作预测的应用
5. 撰写可投稿的综述论文（中/英文初稿）

**阶段 1：D_1 数据包构建**（综述完成后启动）
**阶段 2：D_2 数据包构建**
**阶段 3：模型设计与训练**
**阶段 4：软件开发与部署**
**阶段 5：湿实验验证与迭代**

---

## 11. 与 Cowork（桌面应用）的协作分工

| 工作类型 | 用哪个 |
|---------|--------|
| 项目规划、文献检索、综述撰写、Word 报告 | Cowork（桌面应用） |
| 在 `~/projects/virus_project` 写代码、调试、git | Claude Code（你，在终端） |
| 跑 Python 训练脚本、批量处理基因组数据 | Claude Code |
| 制作 PPT 答辩、申报书修改 | Cowork |

两边的 SSOT（single source of truth）是这份 `CLAUDE.md` 文件 + Cowork 的记忆系统。每次重要进展请同步更新本文件的"第 4 节 当前真实进度"。
