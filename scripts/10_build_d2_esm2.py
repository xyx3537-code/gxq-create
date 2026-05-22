"""
使用 ESM-2 蛋白质语言模型提取 D2 特征，替代手工理化特征。

ESM-2 是 Meta 发布的蛋白质语言模型，把氨基酸序列转化为
高维语义向量（embedding），隐含序列的结构与功能信息。

策略：
  1. 每条蛋白序列 → ESM-2 → 逐残基向量 → 均值池化 → 320 维蛋白向量
  2. 每个病毒 → 对其蛋白向量取均值 → 320 维病毒 D2 向量

为加速 CPU 推理：
  - 每病毒最多随机采样 MAX_PROTEINS 条蛋白（超过则随机取）
  - 序列截断至 MAX_LEN 个氨基酸
  - 批量推理（BATCH_SIZE 条蛋白一起送入模型）

输入：
  data/raw/virus_proteins.fasta
  data/raw/protein_meta.csv

输出：
  data/processed/d2_esm2_features.csv  — 每行一个病毒，320 列 embedding
"""

import random
import numpy as np
import pandas as pd
from collections import defaultdict
from Bio import SeqIO
import torch
from transformers import AutoTokenizer, AutoModel

# ── 配置 ─────────────────────────────────────────────────
MODEL_NAME   = "facebook/esm2_t6_8M_UR50D"  # 8M 参数，320 维，CPU 友好
MAX_PROTEINS = 15    # 每病毒最多取 15 条蛋白（平衡速度与代表性）
MAX_LEN      = 512   # 序列最大长度（aa），超过则截断
BATCH_SIZE   = 16    # 一批推理多少条蛋白
SEED         = 42

PROTEIN_FASTA = "data/raw/virus_proteins.fasta"
PROTEIN_META  = "data/raw/protein_meta.csv"
OUTPUT        = "data/processed/d2_esm2_features.csv"

random.seed(SEED)
AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")


def clean_seq(seq):
    """去除非标准氨基酸，截断至 MAX_LEN"""
    cleaned = ''.join(c for c in seq.upper() if c in AMINO_ACIDS)
    return cleaned[:MAX_LEN]


def embed_batch(seqs, tokenizer, model):
    """
    对一批蛋白序列生成 ESM-2 embedding。
    返回 numpy 数组，形状 (len(seqs), 320)。
    """
    inputs = tokenizer(
        seqs,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=MAX_LEN + 2,  # +2 为特殊 token 留位
    )
    with torch.no_grad():
        outputs = model(**inputs)
    # last_hidden_state: (N, seq_len, 320)
    # 用 attention_mask 做均值池化，忽略 padding 位
    hidden = outputs.last_hidden_state          # (N, L, 320)
    mask   = inputs["attention_mask"].unsqueeze(-1).float()  # (N, L, 1)
    pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1)   # (N, 320)
    return pooled.numpy()


def main():
    print("── 第一步：加载 ESM-2 模型（首次运行需从网络下载 ~31 MB）──")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model     = AutoModel.from_pretrained(MODEL_NAME)
    model.eval()
    print(f"  模型已加载：{MODEL_NAME}")

    print("\n── 第二步：读取蛋白质序列与元数据 ──")
    meta_df   = pd.read_csv(PROTEIN_META)
    id_to_info = {
        row["protein_id"]: (row["accession"], row["host_type"])
        for _, row in meta_df.iterrows()
    }
    print(f"  元数据：{len(id_to_info)} 条蛋白")

    # 按病毒分组收集序列
    virus_seqs = defaultdict(list)   # accession → list of (seq, host)
    virus_host = {}
    skipped = 0

    for record in SeqIO.parse(PROTEIN_FASTA, "fasta"):
        prot_id = record.id.split("|")[0]
        if prot_id not in id_to_info:
            skipped += 1
            continue
        accession, host_type = id_to_info[prot_id]
        seq = clean_seq(str(record.seq))
        if len(seq) < 10:
            skipped += 1
            continue
        virus_seqs[accession].append(seq)
        virus_host[accession] = host_type

    print(f"  有效病毒数：{len(virus_seqs)}，跳过 {skipped} 条蛋白")

    print(f"\n── 第三步：ESM-2 推理（每病毒最多 {MAX_PROTEINS} 条蛋白）──")
    rows = []
    total_viruses = len(virus_seqs)

    for vi, (accession, seqs) in enumerate(virus_seqs.items()):
        # 超过上限时随机采样
        if len(seqs) > MAX_PROTEINS:
            seqs = random.sample(seqs, MAX_PROTEINS)

        # 批量推理
        prot_embeddings = []
        for i in range(0, len(seqs), BATCH_SIZE):
            batch = seqs[i: i + BATCH_SIZE]
            emb   = embed_batch(batch, tokenizer, model)  # (B, 320)
            prot_embeddings.append(emb)

        # 对该病毒所有蛋白向量取均值 → 病毒级 D2 向量
        virus_vec = np.concatenate(prot_embeddings, axis=0).mean(axis=0)  # (320,)

        row = {"accession": accession, "host_type": virus_host[accession]}
        for j, val in enumerate(virus_vec):
            row[f"esm_{j}"] = float(val)
        rows.append(row)

        if (vi + 1) % 20 == 0 or (vi + 1) == total_viruses:
            print(f"  进度：{vi + 1}/{total_viruses} 个病毒")

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT, index=False)

    print(f"\n✅ ESM-2 D2 特征表已保存：{OUTPUT}")
    print(f"   形状：{df.shape[0]} 条病毒 × {df.shape[1]} 列（2 元数据 + 320 维 embedding）")
    print(f"\n── 各宿主类型样本数 ──")
    print(df["host_type"].value_counts().to_string())


if __name__ == "__main__":
    main()
