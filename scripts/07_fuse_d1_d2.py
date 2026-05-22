"""
D1 + D2 后期融合（Late Fusion）：对比四种策略。

策略：
  A. 仅 D1（baseline）
  B. 仅 D2（baseline）
  C. 均等融合：D1 概率 × 0.5 + D2 概率 × 0.5
  D. 加权融合：搜索最优权重 w，使准确率最高

输入：
  data/processed/features.csv     — D1 k-mer 特征
  data/processed/d2_features.csv  — D2 蛋白质理化特征

输出：
  results/fusion_report.txt       — 四策略对比报告
"""

import re
import os
import numpy as np
import pandas as pd
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

os.makedirs("results", exist_ok=True)

D1_FILE     = "data/processed/features.csv"
D2_FILE     = "data/processed/d2_features.csv"
REPORT_FILE = "results/fusion_report.txt"

HOST_TYPES = ["fungi", "algae", "protozoa", "bacteria"]


def strip_host_suffix(seq_id):
    """把 'NC_116874.1_fungi' → 'NC_116874.1'"""
    return re.sub(r'_(' + '|'.join(HOST_TYPES) + r')$', '', seq_id)


def make_pipeline():
    return Pipeline([
        ("scaler", StandardScaler()),
        ("svm",   SVC(kernel="rbf", C=10, gamma="scale",
                      class_weight="balanced", probability=True,
                      random_state=42)),
    ])


def cv_proba(X, y_enc, cv):
    """5折交叉验证，返回各折 OOF（out-of-fold）概率矩阵"""
    n_classes = len(np.unique(y_enc))
    proba_oof = np.zeros((len(y_enc), n_classes))
    for train_idx, val_idx in cv.split(X, y_enc):
        clf = make_pipeline()
        clf.fit(X[train_idx], y_enc[train_idx])
        proba_oof[val_idx] = clf.predict_proba(X[val_idx])
    return proba_oof


def main():
    # ── 1. 加载数据 ──────────────────────────────────────
    d1 = pd.read_csv(D1_FILE)
    d2 = pd.read_csv(D2_FILE)

    d1["accession"] = d1["sequence_id"].apply(strip_host_suffix)
    d2 = d2.rename(columns={"accession": "accession"})

    # 取交集：只保留两个数据集都有的病毒
    common = set(d1["accession"]) & set(d2["accession"])
    print(f"D1 病毒数：{len(d1)}，D2 病毒数：{len(d2)}")
    print(f"交集病毒数：{len(common)}")

    d1 = d1[d1["accession"].isin(common)].copy()
    d2 = d2[d2["accession"].isin(common)].copy()

    # 解决 D1 中同一 accession 出现多次（被多个宿主查询命中）的情况：
    # 以 D2 的标签为权威，只保留与 D2 标签一致的 D1 行
    d2_label = dict(zip(d2["accession"], d2["host_type"]))
    d1 = d1[d1.apply(lambda r: d2_label.get(r["accession"]) == r["host_type"], axis=1)]
    print(f"去重后 D1 剩余：{len(d1)} 条")

    # 按 accession 对齐，确保顺序一致
    d1 = d1.sort_values("accession").reset_index(drop=True)
    d2 = d2.sort_values("accession").reset_index(drop=True)

    assert len(d1) == len(d2), f"对齐后行数不等：D1={len(d1)}, D2={len(d2)}"
    assert (d1["host_type"].values == d2["host_type"].values).all(), \
        "D1/D2 宿主标签不一致，请检查数据！"

    y = d1["host_type"].values
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    classes = le.classes_
    print(f"使用类别：{list(classes)}")

    # ── 2. 提取特征矩阵 ──────────────────────────────────
    drop_d1 = ["sequence_id", "host_type", "accession"]
    drop_d2 = ["accession", "host_type"]
    X1 = d1.drop(columns=drop_d1).values.astype(float)
    X2 = d2.drop(columns=drop_d2).values.astype(float)
    print(f"D1 特征维度：{X1.shape[1]}，D2 特征维度：{X2.shape[1]}")

    # ── 3. 5折交叉验证获取 OOF 概率 ──────────────────────
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    print("\n正在计算 D1 OOF 概率...")
    p1 = cv_proba(X1, y_enc, cv)
    print("正在计算 D2 OOF 概率...")
    p2 = cv_proba(X2, y_enc, cv)

    # ── 4. 四种策略评估 ──────────────────────────────────
    results = {}

    # A: 仅 D1
    acc_a = accuracy_score(y_enc, p1.argmax(axis=1))
    results["A_D1_only"] = acc_a

    # B: 仅 D2
    acc_b = accuracy_score(y_enc, p2.argmax(axis=1))
    results["B_D2_only"] = acc_b

    # C: 均等融合 (w=0.5)
    p_equal = 0.5 * p1 + 0.5 * p2
    acc_c = accuracy_score(y_enc, p_equal.argmax(axis=1))
    results["C_equal_fusion"] = acc_c

    # D: 搜索最优权重（w for D1，1-w for D2）
    best_w, best_acc = 0.5, acc_c
    for w in np.arange(0.0, 1.01, 0.05):
        p_w = w * p1 + (1 - w) * p2
        acc_w = accuracy_score(y_enc, p_w.argmax(axis=1))
        if acc_w > best_acc:
            best_acc = acc_w
            best_w = w
    results["D_best_weight"] = best_acc
    p_best = best_w * p1 + (1 - best_w) * p2

    # ── 5. 输出结果 ───────────────────────────────────────
    print("\n" + "=" * 50)
    print("  融合策略对比（样本数 = %d）" % len(y))
    print("=" * 50)
    labels = {
        "A_D1_only":      "A. 仅 D1（k-mer）",
        "B_D2_only":      "B. 仅 D2（蛋白质理化）",
        "C_equal_fusion": "C. 均等融合（0.5×D1 + 0.5×D2）",
        "D_best_weight":  f"D. 最优融合（{best_w:.2f}×D1 + {1-best_w:.2f}×D2）",
    }
    for key, name in labels.items():
        acc = results[key]
        marker = " ◀ 最优" if acc == max(results.values()) else ""
        print(f"  {name:<38}: {acc*100:.1f}%{marker}")

    print(f"\n── 最优融合分类报告 ──")
    y_pred_best = le.inverse_transform(p_best.argmax(axis=1))
    print(classification_report(y, y_pred_best, target_names=classes))

    # 保存报告
    with open(REPORT_FILE, "w") as f:
        f.write("融合策略对比\n" + "=" * 50 + "\n")
        for key, name in labels.items():
            acc = results[key]
            f.write(f"{name}: {acc*100:.1f}%\n")
        f.write(f"\n最优权重 w(D1) = {best_w:.2f}\n\n")
        f.write("最优融合分类报告:\n")
        f.write(classification_report(y, y_pred_best, target_names=classes))

    print(f"\n✅ 融合报告已保存：{REPORT_FILE}")


if __name__ == "__main__":
    main()
