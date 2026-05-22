"""
从 NCBI 下载病毒蛋白质序列，用于 D2 数据包构建。

输入：data/raw/real_virus_meta.csv（含 accession 列）
输出：
  data/raw/virus_proteins.fasta  — 蛋白质序列（每条病毒可能有多个蛋白）
  data/raw/protein_meta.csv      — 蛋白质 ID → 病毒 accession → 宿主类型 的对应表
"""

import time
import csv
import pandas as pd
from Bio import Entrez, SeqIO

Entrez.email = "yixuan.xu01@student.adelaide.edu.au"

META_FILE      = "data/raw/real_virus_meta.csv"
OUTPUT_FASTA   = "data/raw/virus_proteins.fasta"
OUTPUT_META    = "data/raw/protein_meta.csv"

MIN_PROTEIN_LEN = 50   # 过滤掉小于 50 氨基酸的碎片蛋白


def fetch_proteins(accession):
    """用 accession 号从 NCBI 取回该病毒基因组的所有注释蛋白序列"""
    try:
        handle = Entrez.efetch(
            db="nucleotide", id=accession,
            rettype="gb", retmode="text"   # GenBank 格式含蛋白质注释
        )
        gb_record = SeqIO.read(handle, "genbank")
        handle.close()

        proteins = []
        for feature in gb_record.features:
            if feature.type != "CDS":
                continue
            if "translation" not in feature.qualifiers:
                continue
            aa_seq = feature.qualifiers["translation"][0]
            if len(aa_seq) < MIN_PROTEIN_LEN:
                continue
            # 取蛋白名称（优先 product，没有就用 gene）
            product = feature.qualifiers.get(
                "product", feature.qualifiers.get("gene", ["unknown"])
            )[0]
            prot_id = feature.qualifiers.get("protein_id", [f"{accession}_prot"])[0]
            proteins.append({
                "protein_id": prot_id,
                "accession":  accession,
                "product":    product,
                "sequence":   aa_seq,
                "length":     len(aa_seq),
            })
        return proteins

    except Exception as e:
        print(f"  ⚠ {accession} 下载失败：{e}")
        return []


def main():
    meta_df = pd.read_csv(META_FILE)
    # 去重：同一个 accession 可能对应多条序列（不同宿主标签行）
    accession_host = meta_df.drop_duplicates("accession")[["accession", "host_type"]]
    print(f"共 {len(accession_host)} 个不重复 accession，开始下载蛋白质...")

    all_proteins = []
    host_map = dict(zip(accession_host["accession"], accession_host["host_type"]))

    for i, (acc, host) in enumerate(host_map.items()):
        proteins = fetch_proteins(acc)
        for p in proteins:
            p["host_type"] = host
        all_proteins.extend(proteins)

        if (i + 1) % 10 == 0:
            print(f"  进度：{i+1}/{len(host_map)}，已获取 {len(all_proteins)} 条蛋白")
        time.sleep(0.35)   # 避免被 NCBI 限速

    print(f"\n下载完成，共 {len(all_proteins)} 条蛋白质序列")

    # 写出 FASTA（ID 格式：protein_id|host_type）
    with open(OUTPUT_FASTA, "w") as f:
        for p in all_proteins:
            f.write(f">{p['protein_id']}|{p['host_type']}\n")
            # 每 60 字符换行，符合标准 FASTA 格式
            seq = p["sequence"]
            for j in range(0, len(seq), 60):
                f.write(seq[j:j+60] + "\n")

    # 写出元数据
    with open(OUTPUT_META, "w", newline="") as f:
        fields = ["protein_id", "accession", "host_type", "product", "length"]
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_proteins)

    print(f"✅ FASTA 已保存：{OUTPUT_FASTA}")
    print(f"✅ 元数据已保存：{OUTPUT_META}")
    print(f"\n── 各宿主类型蛋白数量 ──")
    from collections import Counter
    counts = Counter(p["host_type"] for p in all_proteins)
    for h, n in sorted(counts.items()):
        print(f"  {h:12s}: {n} 条蛋白")


if __name__ == "__main__":
    main()
