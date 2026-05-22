"""
从病毒蛋白质序列提取 D2 特征，输出病毒级别的特征表。

策略：每个病毒有多条蛋白质，对每条蛋白提取特征后，
取该病毒所有蛋白特征的均值，作为该病毒的 D2 特征向量。

输入：
  data/raw/virus_proteins.fasta   — 蛋白质序列
  data/raw/protein_meta.csv       — 蛋白质 ID → 病毒 accession → 宿主类型

输出：
  data/processed/d2_features.csv  — D2 特征表（每行一个病毒）

特征说明（每条蛋白提取后取均值）：
  - 氨基酸组成 (20)  : 20种氨基酸各自的比例
  - 理化性质 (5)     : 分子量、等电点、GRAVY疏水指数、不稳定指数、芳香性
  - 蛋白数量 (1)     : 该病毒编码的蛋白总数
  - 平均蛋白长度 (1) : 所有蛋白的平均长度（氨基酸数）
共 27 维特征
"""

import pandas as pd
import numpy as np
from Bio import SeqIO
from Bio.SeqUtils.ProtParam import ProteinAnalysis
from collections import defaultdict

PROTEIN_FASTA = "data/raw/virus_proteins.fasta"
PROTEIN_META  = "data/raw/protein_meta.csv"
OUTPUT        = "data/processed/d2_features.csv"

AMINO_ACIDS = list("ACDEFGHIKLMNPQRSTVWY")


def extract_protein_features(aa_seq):
    """对单条蛋白质序列提取理化特征，返回字典"""
    # 过滤非标准氨基酸（X、*等），ProteinAnalysis 不接受
    clean_seq = ''.join(c for c in aa_seq.upper() if c in AMINO_ACIDS)
    if len(clean_seq) < 10:
        return None

    try:
        pa = ProteinAnalysis(clean_seq)
        aa_comp = pa.amino_acids_percent         # 20 种氨基酸比例
        features = {aa: aa_comp.get(aa, 0.0) for aa in AMINO_ACIDS}
        features["mol_weight"]       = pa.molecular_weight()
        features["isoelectric_point"] = pa.isoelectric_point()
        features["gravy"]            = pa.gravy()             # 疏水性
        features["instability_index"] = pa.instability_index()
        features["aromaticity"]      = pa.aromaticity()
        return features
    except Exception:
        return None


def main():
    # 1. 读取元数据：建立 protein_id → (accession, host_type) 映射
    meta_df = pd.read_csv(PROTEIN_META)
    id_to_info = {
        row["protein_id"]: (row["accession"], row["host_type"])
        for _, row in meta_df.iterrows()
    }
    print(f"蛋白质元数据加载完成：{len(id_to_info)} 条")

    # 2. 遍历蛋白质 FASTA，按病毒分组收集特征
    # virus_feats: accession → list of feature dicts
    virus_feats  = defaultdict(list)
    virus_host   = {}
    skipped = 0

    print("正在提取蛋白质特征（耐心等待，共数万条蛋白）...")
    for i, record in enumerate(SeqIO.parse(PROTEIN_FASTA, "fasta")):
        # FASTA ID 格式：protein_id|host_type
        prot_id = record.id.split("|")[0]
        if prot_id not in id_to_info:
            skipped += 1
            continue

        accession, host_type = id_to_info[prot_id]
        feats = extract_protein_features(str(record.seq))
        if feats is None:
            skipped += 1
            continue

        virus_feats[accession].append(feats)
        virus_host[accession] = host_type

        if (i + 1) % 5000 == 0:
            print(f"  已处理 {i+1} 条蛋白...")

    print(f"  跳过 {skipped} 条（序列异常）")
    print(f"  有效病毒数：{len(virus_feats)}")

    # 3. 对每个病毒取所有蛋白特征的均值，汇聚成一行
    rows = []
    feature_cols = AMINO_ACIDS + ["mol_weight", "isoelectric_point",
                                   "gravy", "instability_index", "aromaticity"]

    for accession, feat_list in virus_feats.items():
        feat_matrix = pd.DataFrame(feat_list)[feature_cols]
        row = {"accession": accession,
               "host_type": virus_host[accession],
               "protein_count": len(feat_list)}
        row["mean_length"] = meta_df[meta_df["accession"] == accession]["length"].mean()
        for col in feature_cols:
            row[col] = feat_matrix[col].mean()
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT, index=False)

    print(f"\n✅ D2 特征表已保存：{OUTPUT}")
    print(f"   形状：{df.shape[0]} 条病毒 × {df.shape[1]} 列")
    print(f"\n── 各宿主类型样本数 ──")
    print(df["host_type"].value_counts().to_string())
    print(f"\n── 特征列预览 ──")
    print(df[["accession", "host_type", "protein_count", "mean_length",
              "gravy", "isoelectric_point"]].head())


if __name__ == "__main__":
    main()
