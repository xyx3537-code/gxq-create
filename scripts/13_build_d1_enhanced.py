"""
D1 增强特征提取：k-mer 扩展 + 序列组成偏斜。

在原有 3-mer（64 维）基础上，新增：
  - 单碱基频率（4 维）  : A/T/G/C 各自比例
  - 2-mer 频率（16 维） : 二核苷酸，捕捉 CpG 抑制等偏好
  - 4-mer 频率（256 维）: 高分辨率 k-mer，是 VirHostMatcher 核心特征
  - GC-skew（1 维）     : (G-C)/(G+C)，反映链不对称性
  - AT-skew（1 维）     : (A-T)/(A+T)

共 2 + 4 + 16 + 64 + 256 + 2 = 344 维特征（含 length + gc_content）

输入：
  data/raw/real_virus.fasta
  data/raw/real_virus_meta.csv

输出：
  data/processed/d1_enhanced_features.csv
"""

import itertools
import pandas as pd
from collections import Counter
from Bio import SeqIO

FASTA_FILE = "data/raw/real_virus.fasta"
META_FILE  = "data/raw/real_virus_meta.csv"
OUTPUT     = "data/processed/d1_enhanced_features.csv"

# 预生成各阶 k-mer 列表（固定顺序，保证训练/预测列对齐）
ALL_1MERS = list("ACGT")
ALL_2MERS = [''.join(k) for k in itertools.product('ACGT', repeat=2)]
ALL_3MERS = [''.join(k) for k in itertools.product('ACGT', repeat=3)]
ALL_4MERS = [''.join(k) for k in itertools.product('ACGT', repeat=4)]


def kmer_freq(seq, kmers, k):
    """计算指定阶 k-mer 的相对频率"""
    total = len(seq) - k + 1
    if total <= 0:
        return {km: 0.0 for km in kmers}
    counts = Counter(seq[i:i+k] for i in range(total))
    return {km: counts.get(km, 0) / total for km in kmers}


def gc_skew(seq):
    """GC-skew = (G-C)/(G+C)，衡量链不对称性"""
    g, c = seq.count('G'), seq.count('C')
    return (g - c) / (g + c) if (g + c) > 0 else 0.0


def at_skew(seq):
    """AT-skew = (A-T)/(A+T)"""
    a, t = seq.count('A'), seq.count('T')
    return (a - t) / (a + t) if (a + t) > 0 else 0.0


def extract_features(seq):
    """提取一条序列的全部 D1 增强特征，返回字典"""
    length = len(seq)
    gc     = (seq.count('G') + seq.count('C')) / length if length > 0 else 0.0

    row = {
        "length":    length,
        "gc_content": round(gc * 100, 2),
        "gc_skew":   round(gc_skew(seq), 6),
        "at_skew":   round(at_skew(seq), 6),
    }

    row.update({f"1mer_{k}": v for k, v in kmer_freq(seq, ALL_1MERS, 1).items()})
    row.update({f"2mer_{k}": v for k, v in kmer_freq(seq, ALL_2MERS, 2).items()})
    row.update({f"3mer_{k}": v for k, v in kmer_freq(seq, ALL_3MERS, 3).items()})
    row.update({f"4mer_{k}": v for k, v in kmer_freq(seq, ALL_4MERS, 4).items()})
    return row


def main():
    meta_df    = pd.read_csv(META_FILE)
    id_to_host = dict(zip(meta_df["sequence_id"], meta_df["host_type"]))
    print(f"元数据加载完成：{len(id_to_host)} 条记录")

    rows, skipped = [], 0
    for record in SeqIO.parse(FASTA_FILE, "fasta"):
        seq_id = record.id
        seq    = str(record.seq).upper()

        if seq_id not in id_to_host:
            skipped += 1
            continue
        if seq.count('N') / len(seq) > 0.1:
            skipped += 1
            continue

        row = {"sequence_id": seq_id, "host_type": id_to_host[seq_id]}
        row.update(extract_features(seq))
        rows.append(row)

    if skipped:
        print(f"⚠ 跳过 {skipped} 条序列")

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT, index=False)

    feat_cols = [c for c in df.columns if c not in ("sequence_id", "host_type")]
    print(f"\n✅ 增强 D1 特征表已保存：{OUTPUT}")
    print(f"   形状：{df.shape[0]} 条序列 × {len(feat_cols)} 维特征")
    print(f"\n── 特征维度明细 ──")
    print(f"  基础统计（length, gc_content, gc_skew, at_skew）: 4")
    print(f"  1-mer : {len(ALL_1MERS)}")
    print(f"  2-mer : {len(ALL_2MERS)}")
    print(f"  3-mer : {len(ALL_3MERS)}")
    print(f"  4-mer : {len(ALL_4MERS)}")
    print(f"  合计  : {len(feat_cols)}")
    print(f"\n── 各宿主类型样本数 ──")
    print(df["host_type"].value_counts().to_string())


if __name__ == "__main__":
    main()
