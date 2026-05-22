"""
从 NCBI 下载已知宿主的病毒基因组序列，用于 D1 数据包构建。

目标宿主类型：真菌（Fungi）、藻类（Algae/Protist）、原生动物（Protozoa）、细菌（Bacteria）
             植物（Plant）、无脊椎动物（Invertebrate）
下载内容：病毒核苷酸序列（FASTA）+ 宿主标注（CSV）
"""

import os
import time
import csv
from Bio import Entrez, SeqIO

# ── 配置 ──────────────────────────────────────────────────────────────────────
Entrez.email = "yixuan.xu01@student.adelaide.edu.au"   # NCBI 要求填邮箱

OUTPUT_FASTA = "data/raw/real_virus.fasta"
OUTPUT_META  = "data/raw/real_virus_meta.csv"

# 每类宿主的搜索词 → 宿主标签
# protozoa 不能用 protozoa[Host]（NCBI 不认），需列举具体宿主属名
QUERIES = {
    "fungi":       'viruses[Organism] AND fungi[Host] AND complete genome[Title]',
    "algae":       'viruses[Organism] AND (Chlorella[Host] OR Ectocarpus[Host] OR Heterosigma[Host] OR Micromonas[Host] OR Emiliania[Host] OR Ostreococcus[Host])',
    "protozoa":    'viruses[Organism] AND (Leishmania[Host] OR Trichomonas[Host] OR Giardia[Host] OR Cryptosporidium[Host]) AND complete genome[Title]',
    "bacteria":    'viruses[Organism] AND bacteria[Host] AND complete genome[Title]',
    "plant":       'viruses[Organism] AND (Arabidopsis[Host] OR Nicotiana[Host] OR Solanum[Host] OR Oryza[Host] OR Zea[Host]) AND complete genome[Title]',
    "invertebrate":'viruses[Organism] AND (Drosophila[Host] OR Aedes[Host] OR Bombyx[Host] OR Apis[Host]) AND complete genome[Title]',
}

MAX_PER_CLASS = 150  # 每类最多下载多少条（扩充数据集）
MIN_LEN       = 1000 # 过滤掉长度不足 1000 bp 的序列（太短没意义）
# ─────────────────────────────────────────────────────────────────────────────


def search_ncbi(query, max_results):
    """在 NCBI Nucleotide 数据库搜索，返回 accession ID 列表"""
    handle = Entrez.esearch(db="nucleotide", term=query, retmax=max_results)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]


def fetch_sequences(id_list):
    """批量下载序列，返回 SeqRecord 列表"""
    ids = ",".join(id_list)
    handle = Entrez.efetch(db="nucleotide", id=ids, rettype="fasta", retmode="text")
    records = list(SeqIO.parse(handle, "fasta"))
    handle.close()
    return records


def main():
    os.makedirs("data/raw", exist_ok=True)

    all_records = []  # 所有 SeqRecord
    all_meta    = []  # 对应的元数据（id, host_type, length）

    for host_type, query in QUERIES.items():
        print(f"\n[{host_type}] 正在搜索 NCBI...")

        # 1. 搜索获取 ID 列表
        id_list = search_ncbi(query, MAX_PER_CLASS * 3)  # 多搜一些，过滤后留够
        print(f"  找到 {len(id_list)} 条记录，开始下载序列...")

        if not id_list:
            print(f"  ⚠ 未找到 {host_type} 相关记录，跳过")
            continue

        # 2. 分批下载（每批 10 条，避免超时）
        batch_size = 10
        fetched = []
        for i in range(0, len(id_list), batch_size):
            batch = id_list[i:i + batch_size]
            try:
                records = fetch_sequences(batch)
                fetched.extend(records)
                print(f"  已下载 {min(i + batch_size, len(id_list))}/{len(id_list)} 条")
                time.sleep(0.4)  # 礼貌性延迟，避免被 NCBI 限速
            except Exception as e:
                print(f"  ⚠ 批次 {i} 下载失败：{e}，跳过")
                continue

        # 3. 过滤太短的序列，保留前 MAX_PER_CLASS 条
        kept = 0
        for rec in fetched:
            if kept >= MAX_PER_CLASS:
                break
            seq_len = len(rec.seq)
            if seq_len < MIN_LEN:
                continue
            # 改写 ID，避免空格导致后续解析出错
            clean_id = rec.id.split()[0]
            rec.id = f"{clean_id}_{host_type}"
            rec.description = ""
            all_records.append(rec)
            all_meta.append({
                "sequence_id": rec.id,
                "host_type":   host_type,
                "length":      seq_len,
                "accession":   clean_id,
            })
            kept += 1

        print(f"  ✓ 保留 {kept} 条有效序列（长度 ≥ {MIN_LEN} bp）")

    # 4. 写出 FASTA
    SeqIO.write(all_records, OUTPUT_FASTA, "fasta")
    print(f"\n✅ FASTA 已保存：{OUTPUT_FASTA}（共 {len(all_records)} 条）")

    # 5. 写出元数据 CSV
    with open(OUTPUT_META, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["sequence_id", "host_type", "length", "accession"])
        writer.writeheader()
        writer.writerows(all_meta)
    print(f"✅ 元数据已保存：{OUTPUT_META}")

    # 6. 统计各类数量
    print("\n── 各宿主类型统计 ──")
    from collections import Counter
    counts = Counter(m["host_type"] for m in all_meta)
    for h, n in counts.items():
        print(f"  {h:12s}: {n} 条")


if __name__ == "__main__":
    main()
