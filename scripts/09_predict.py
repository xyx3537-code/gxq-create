"""
单条病毒宿主预测函数，供 Flask API 直接调用。

D2 特征版本：ESM-2（facebook/esm2_t6_8M_UR50D，320 维）
融合权重：D1=0.4，D2=0.6（v2，基于 ESM-2 D2 优化后的最优权重）

输入：
  genome_seq   — 病毒基因组序列（DNA 字符串）
  protein_seqs — 该病毒的蛋白质序列列表（氨基酸字符串，可为空列表）

输出：
  {
    "predicted_host": "fungi",
    "confidence": 0.87,
    "probabilities": {"algae": 0.05, "bacteria": 0.03, "fungi": 0.87, "protozoa": 0.05},
    "d1_contribution": 0.40,
    "d2_contribution": 0.60
  }
"""

import json
import joblib
import numpy as np
import torch
from itertools import product
from transformers import AutoTokenizer, AutoModel
from Bio.Seq import Seq

# ── 加载模型（模块级，进程启动时只加载一次）────────────────
_clf_d1 = joblib.load("models/d1_pipeline.joblib")
_d2_bundle = joblib.load("models/d2_esm2_pipeline.joblib")
_clf_d2 = _d2_bundle["pipeline"]
_le     = joblib.load("models/label_encoder.joblib")

with open("models/fusion_weight.json") as f:
    _fw = json.load(f)
with open("models/feature_meta.json") as f:
    _meta = json.load(f)

W_D1 = _fw["w_d1"]
W_D2 = _fw["w_d2"]
D1_FEATURES = _meta["d1_features"]

# ESM-2 蛋白质语言模型
_ESM2_NAME   = "facebook/esm2_t6_8M_UR50D"
_MAX_LEN     = 512   # 序列截断长度（aa）
_BATCH_SIZE  = 16
_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")

print(f"[GXQ_Create] 加载 ESM-2 模型：{_ESM2_NAME}")
_tokenizer = AutoTokenizer.from_pretrained(_ESM2_NAME)
_esm2      = AutoModel.from_pretrained(_ESM2_NAME)
_esm2.eval()
print("[GXQ_Create] 模型加载完成")


# ── DNA → 蛋白质自动翻译 ─────────────────────────────────
_MIN_ORF_AA = 100   # 最短有效 ORF 长度（氨基酸）
_MAX_PROTS   = 15   # 最多送入 ESM-2 的蛋白数量

def translate_dna_to_proteins(dna_seq: str) -> list:
    """
    在 6 个阅读框中寻找 ORF 并翻译为氨基酸序列。
    - 正链 3 个框 + 反互补链 3 个框，共扫描 6 次
    - 每个 ORF 从第一个 M（甲硫氨酸）开始，到终止密码子结束
    - 返回按长度降序排列的前 _MAX_PROTS 条序列
    """
    seq = Seq(dna_seq.upper().replace(" ", "").replace("\n", ""))
    proteins = []
    for nuc in (seq, seq.reverse_complement()):
        for frame in range(3):
            trimmed = nuc[frame:]
            trimmed = trimmed[:len(trimmed) - len(trimmed) % 3]  # 截成 3 的倍数
            trans = str(trimmed.translate())
            for orf in trans.split("*"):
                if "M" not in orf:
                    continue
                prot = orf[orf.index("M"):]
                if len(prot) >= _MIN_ORF_AA:
                    proteins.append(prot)
    proteins.sort(key=len, reverse=True)
    return proteins[:_MAX_PROTS]


# ── D1 特征提取 ──────────────────────────────────────────
def _build_kmers(k=3):
    return [''.join(p) for p in product("ACGT", repeat=k)]

_ALL_KMERS = _build_kmers(3)

def extract_d1_features(genome_seq: str) -> np.ndarray:
    seq    = genome_seq.upper().replace(" ", "").replace("\n", "")
    length = len(seq)
    gc     = (seq.count("G") + seq.count("C")) / length * 100 if length > 0 else 0.0

    total  = length - 2
    counts = {km: 0 for km in _ALL_KMERS}
    for i in range(total):
        km = seq[i:i+3]
        if km in counts:
            counts[km] += 1
    kmer_freq = {km: (c / total if total > 0 else 0.0) for km, c in counts.items()}

    row = {"length": length, "gc_content": gc}
    row.update(kmer_freq)
    return np.array([row[col] for col in D1_FEATURES], dtype=float).reshape(1, -1)


# ── D2 特征提取（ESM-2）──────────────────────────────────
def extract_d2_features(protein_seqs: list) -> np.ndarray:
    """
    用 ESM-2 将蛋白质序列转为 320 维向量。
    无有效蛋白质时返回零向量（降级处理，准确率会下降）。
    """
    clean = []
    for s in protein_seqs:
        c = ''.join(x for x in s.upper() if x in _AMINO_ACIDS)[:_MAX_LEN]
        if len(c) >= 10:
            clean.append(c)

    if not clean:
        return np.zeros((1, 320), dtype=float)

    prot_vecs = []
    for i in range(0, len(clean), _BATCH_SIZE):
        batch  = clean[i: i + _BATCH_SIZE]
        inputs = _tokenizer(batch, return_tensors="pt", padding=True,
                            truncation=True, max_length=_MAX_LEN + 2)
        with torch.no_grad():
            out = _esm2(**inputs)
        mask   = inputs["attention_mask"].unsqueeze(-1).float()
        pooled = (out.last_hidden_state * mask).sum(1) / mask.sum(1)  # (B, 320)
        prot_vecs.append(pooled.numpy())

    virus_vec = np.concatenate(prot_vecs, axis=0).mean(axis=0)  # (320,)
    return virus_vec.reshape(1, -1)


# ── 主预测函数 ────────────────────────────────────────────
_SHORT_GENOME_THRESHOLD = 5000   # bp；低于此长度 k-mer 统计不可靠

def predict(genome_seq: str, protein_seqs: list) -> dict:
    seq_len = len(genome_seq.replace(" ", "").replace("\n", ""))
    short_genome = seq_len < _SHORT_GENOME_THRESHOLD

    x1 = extract_d1_features(genome_seq)
    p1 = _clf_d1.predict_proba(x1)[0]

    if not protein_seqs:
        # 无注释蛋白质：从基因组 6 个阅读框自动翻译 ORF
        # 这是项目创新点：DNA → 翻译 → ESM-2 embedding → 宿主预测
        # ORF 质量低于 NCBI 注释蛋白，因此提高 D1 权重以保持稳健性
        protein_seqs = translate_dna_to_proteins(genome_seq)
        auto_translated = True
        x2 = extract_d2_features(protein_seqs)
        p2 = _clf_d2.predict_proba(x2)[0]
        w_d1, w_d2 = 0.70, 0.30   # ORF 模式：D1 主导，D2 辅助
        p_fused = w_d1 * p1 + w_d2 * p2
    else:
        # 有注释蛋白质：标准 D1 + D2 融合
        auto_translated = False
        x2 = extract_d2_features(protein_seqs)
        p2 = _clf_d2.predict_proba(x2)[0]
        w_d1, w_d2 = W_D1, W_D2
        p_fused = w_d1 * p1 + w_d2 * p2

    best_idx = int(np.argmax(p_fused))
    classes  = _le.classes_

    # GC 含量（已在 extract_d1_features 中计算，这里重新算一次避免返回值耦合）
    clean_seq = genome_seq.upper().replace(" ", "").replace("\n", "")
    gc_content = round((clean_seq.count("G") + clean_seq.count("C")) / seq_len * 100, 1) if seq_len > 0 else 0.0

    # Top k-mer enrichment（相对于均匀背景 1/64）
    total_kmers = seq_len - 2
    uniform_bg  = 1.0 / 64
    kmer_enrichment = []
    for km in _ALL_KMERS:
        cnt = sum(1 for i in range(total_kmers) if clean_seq[i:i+3] == km)
        freq = cnt / total_kmers if total_kmers > 0 else 0.0
        kmer_enrichment.append((km, round(freq / uniform_bg, 2)))
    kmer_enrichment.sort(key=lambda x: -x[1])
    top_kmers = [{"kmer": km, "enrichment": e} for km, e in kmer_enrichment[:6]]

    return {
        "predicted_host":  classes[best_idx],
        "confidence":      round(float(p_fused[best_idx]), 4),
        "probabilities":   {cls: round(float(prob), 4)
                            for cls, prob in zip(classes, p_fused)},
        "d1_contribution": w_d1,
        "d2_contribution": w_d2,
        "auto_translated": auto_translated,
        "protein_count":   len(protein_seqs),
        "genome_length":   seq_len,
        "gc_content":      gc_content,
        "short_genome":    short_genome,
        "top_kmers":       top_kmers,
    }


# ── 命令行快速测试 ────────────────────────────────────────
if __name__ == "__main__":
    import sys, re, os
    from Bio import SeqIO

    if len(sys.argv) < 2:
        print("用法: python 09_predict.py <genome.fasta> [proteins.fasta]")
        print("\n使用内置示例序列测试...")
        rec = next(SeqIO.parse("data/raw/real_virus.fasta", "fasta"))
        genome_seq   = str(rec.seq)
        protein_seqs = []
        prot_file    = "data/raw/virus_proteins.fasta"
        if os.path.exists(prot_file):
            import pandas as pd
            acc_clean = re.sub(r'_(fungi|algae|protozoa|bacteria|plant|invertebrate)$', '', rec.id.split()[0])
            pmeta     = pd.read_csv("data/raw/protein_meta.csv")
            prot_ids  = set(pmeta[pmeta["accession"] == acc_clean]["protein_id"])
            protein_seqs = [str(r.seq) for r in SeqIO.parse(prot_file, "fasta")
                            if r.id.split("|")[0] in prot_ids]
        print(f"测试病毒：{rec.id}，蛋白质序列数：{len(protein_seqs)}")
    else:
        genome_seq   = str(next(SeqIO.parse(sys.argv[1], "fasta")).seq)
        protein_seqs = ([str(r.seq) for r in SeqIO.parse(sys.argv[2], "fasta")]
                        if len(sys.argv) > 2 else [])

    result = predict(genome_seq, protein_seqs)
    print("\n── 预测结果 ──")
    print(f"  宿主类型 : {result['predicted_host']}")
    print(f"  置信度   : {result['confidence']*100:.1f}%")
    print(f"  各类概率 :")
    for host, prob in sorted(result["probabilities"].items(), key=lambda x: -x[1]):
        bar = "█" * int(prob * 30)
        print(f"    {host:12s} {prob*100:5.1f}%  {bar}")
