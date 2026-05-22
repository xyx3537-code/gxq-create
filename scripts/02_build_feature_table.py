"""
从真实病毒基因组中提取 D1 序列特征，输出带宿主标签的特征表。

输入：
  data/raw/real_virus.fasta      — 真实病毒序列
  data/raw/real_virus_meta.csv   — 序列 ID → 宿主类型的对应表

输出：
  data/processed/features.csv    — 特征表（每行一个病毒，每列一个特征）

特征说明：
  - gc_content   : GC 含量（%），反映基因组碱基组成偏好
  - length       : 序列长度（bp）
  - 3-mer 频率   : 64 种三联碱基的出现频率，是 k-mer 方法的核心特征
"""

import itertools
import pandas as pd
from collections import Counter
from Bio import SeqIO

# ── 输入输出路径 ───────────────────────────────────────────────────────────────
FASTA_FILE = "data/raw/real_virus.fasta"
META_FILE  = "data/raw/real_virus_meta.csv"
OUTPUT     = "data/processed/features.csv"
# ─────────────────────────────────────────────────────────────────────────────

# 预先生成所有 64 种 3-mer（AAA, AAT, AAG, ...），保证特征列顺序固定
ALL_3MERS = [''.join(k) for k in itertools.product('ACGT', repeat=3)]


def calc_kmer_freq(sequence, k=3):
    """计算序列中所有 k-mer 的相对频率（出现次数 / 总 k-mer 数）"""
    kmers = [sequence[i:i+k] for i in range(len(sequence) - k + 1)]
    total = len(kmers)
    if total == 0:
        return {kmer: 0.0 for kmer in ALL_3MERS}
    counts = Counter(kmers)
    # 未出现的 k-mer 补 0，保证每条序列列数相同
    return {kmer: counts.get(kmer, 0) / total for kmer in ALL_3MERS}


def calc_gc(sequence):
    """计算 GC 含量（%）"""
    gc = sequence.count('G') + sequence.count('C')
    return round(gc / len(sequence) * 100, 2) if sequence else 0.0


def main():
    # 1. 读取宿主标注表，建立 sequence_id → host_type 映射
    meta_df = pd.read_csv(META_FILE)
    id_to_host = dict(zip(meta_df["sequence_id"], meta_df["host_type"]))
    print(f"元数据加载完成：{len(id_to_host)} 条记录")

    # 2. 遍历 FASTA，提取特征
    rows = []
    skipped = 0
    for record in SeqIO.parse(FASTA_FILE, "fasta"):
        seq_id = record.id
        sequence = str(record.seq).upper()

        # 跳过 ID 不在元数据中的序列（理论上不会发生）
        if seq_id not in id_to_host:
            skipped += 1
            continue

        # 过滤含非标准碱基的序列（N 过多会干扰 k-mer 统计）
        n_ratio = sequence.count('N') / len(sequence)
        if n_ratio > 0.1:
            skipped += 1
            continue

        kmer_features = calc_kmer_freq(sequence)

        row = {
            "sequence_id": seq_id,
            "host_type":   id_to_host[seq_id],
            "length":      len(sequence),
            "gc_content":  calc_gc(sequence),
        }
        row.update(kmer_features)
        rows.append(row)

    if skipped:
        print(f"⚠ 跳过 {skipped} 条序列（ID 不匹配或 N 碱基过多）")

    # 3. 保存特征表
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT, index=False)

    print(f"\n✅ 特征表已保存：{OUTPUT}")
    print(f"   形状：{df.shape[0]} 条序列 × {df.shape[1]} 列")
    print(f"\n── 各宿主类型样本数 ──")
    print(df["host_type"].value_counts().to_string())
    print(f"\n── 特征列预览（前 5 列）──")
    print(df.iloc[:, :6].head())


if __name__ == "__main__":
    main()
