"""
验证在线预测函数（09_predict.py）的实际表现。
测试内容：
  1. DNA+蛋白质模式准确率（验证 GC bug 修复后结果与训练一致）
  2. 仅 DNA（ORF 自动翻译）模式准确率
  3. 网格搜索 ORF 模式最优 D1/D2 权重
"""

import importlib.util, pathlib, re, sys
import numpy as np
import pandas as pd
from Bio import SeqIO
from collections import defaultdict

# ── 加载预测模块 ──────────────────────────────────────────
spec = importlib.util.spec_from_file_location(
    "predict09", pathlib.Path("scripts/09_predict.py")
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# ── 读取数据 ──────────────────────────────────────────────
meta    = pd.read_csv("data/raw/real_virus_meta.csv")
pmeta   = pd.read_csv("data/raw/protein_meta.csv")

# 建立 accession → proteins 映射
prot_seqs = defaultdict(list)
for rec in SeqIO.parse("data/raw/virus_proteins.fasta", "fasta"):
    pid = rec.id.split("|")[0]
    row = pmeta[pmeta["protein_id"] == pid]
    if not row.empty:
        prot_seqs[row.iloc[0]["accession"]].append(str(rec.seq))

# 建立 accession → genome 映射（从 FASTA）
genome_seqs = {}
for rec in SeqIO.parse("data/raw/real_virus.fasta", "fasta"):
    acc = re.sub(r"_(fungi|algae|protozoa|bacteria|plant|invertebrate)$", "", rec.id)
    genome_seqs[acc] = str(rec.seq)

# ── 每类取前 N 条测试 ────────────────────────────────────
N_PER_CLASS = 15
_valid = meta[meta["accession"].isin(genome_seqs)]
test_samples = pd.concat(
    [g.head(N_PER_CLASS) for _, g in _valid.groupby("host_type")]
).reset_index(drop=True)
print(f"测试样本数：{len(test_samples)} 条")
print(test_samples["host_type"].value_counts().to_string())
print()

# ── 模式1：DNA + 蛋白质 ───────────────────────────────────
print("=" * 50)
print("模式 1：DNA + 注释蛋白质（验证 GC bug 修复）")
print("=" * 50)
correct1, total1 = 0, 0
for _, row in test_samples.iterrows():
    acc, true_host = row["accession"], row["host_type"]
    dna   = genome_seqs.get(acc, "")
    prots = prot_seqs.get(acc, [])
    if not dna or not prots:
        continue
    try:
        r = mod.predict(dna, prots)
        ok = r["predicted_host"] == true_host
        correct1 += ok
        total1 += 1
    except Exception as e:
        print(f"  ⚠ {acc}: {e}")

acc1 = correct1 / total1 * 100 if total1 else 0
print(f"准确率：{correct1}/{total1} = {acc1:.1f}%\n")

# ── 模式2：仅 DNA（ORF 自动翻译，当前权重 0.7/0.3）────────
print("=" * 50)
print("模式 2：仅 DNA（ORF 自动翻译，当前 D1=0.7 D2=0.3）")
print("=" * 50)
correct2, total2 = 0, 0
per_class = defaultdict(lambda: [0, 0])
for _, row in test_samples.iterrows():
    acc, true_host = row["accession"], row["host_type"]
    dna = genome_seqs.get(acc, "")
    if not dna:
        continue
    try:
        r = mod.predict(dna, [])   # 空蛋白质列表 → ORF 模式
        ok = r["predicted_host"] == true_host
        correct2 += ok
        total2 += 1
        per_class[true_host][0] += ok
        per_class[true_host][1] += 1
    except Exception as e:
        print(f"  ⚠ {acc}: {e}")

acc2 = correct2 / total2 * 100 if total2 else 0
print(f"总准确率：{correct2}/{total2} = {acc2:.1f}%")
print("\n各宿主类型准确率：")
for host, (c, t) in sorted(per_class.items()):
    bar = "█" * c + "░" * (t - c)
    print(f"  {host:15s} {c}/{t}  {bar}")
print()

# ── 模式3：网格搜索最优 ORF 权重 ─────────────────────────
print("=" * 50)
print("模式 3：网格搜索 ORF 模式最优 D1 权重")
print("=" * 50)

# 预先计算所有样本的 D1 和 D2 概率（避免重复推理）
print("预计算各样本概率（需要一点时间）...")
sample_probs = []
for _, row in test_samples.iterrows():
    acc, true_host = row["accession"], row["host_type"]
    dna = genome_seqs.get(acc, "")
    if not dna:
        continue
    try:
        x1   = mod.extract_d1_features(dna)
        orfs = mod.translate_dna_to_proteins(dna)
        x2   = mod.extract_d2_features(orfs)
        p1   = mod._clf_d1.predict_proba(x1)[0]
        p2   = mod._clf_d2.predict_proba(x2)[0]
        sample_probs.append((p1, p2, true_host))
    except Exception as e:
        print(f"  ⚠ {acc}: {e}")

classes = list(mod._le.classes_)
best_w, best_acc = 0.7, 0.0
print(f"\n{'D1 权重':>8}  {'D2 权重':>8}  {'准确率':>8}")
for w1 in [i / 10 for i in range(3, 10)]:   # 0.3 ~ 0.9
    w2 = round(1 - w1, 1)
    correct = sum(
        classes[np.argmax(w1 * p1 + w2 * p2)] == true_host
        for p1, p2, true_host in sample_probs
    )
    a = correct / len(sample_probs) * 100
    marker = " ◀ 当前" if w1 == 0.7 else (" ★ 最优" if a > best_acc else "")
    if a > best_acc:
        best_acc, best_w = a, w1
    print(f"  {w1:.1f}       {w2:.1f}       {a:.1f}%{marker}")

print(f"\n最优 D1 权重：{best_w}，准确率：{best_acc:.1f}%")
