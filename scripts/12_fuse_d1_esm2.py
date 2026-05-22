"""
D1（k-mer）+ D2-ESM2（蛋白质 embedding）后期融合，与原 95.4% 结果对比。

策略：对每个样本分别用 D1 模型和 D2-ESM2 模型预测概率，
然后加权平均（网格搜索最优权重）。

输入：
  data/processed/features.csv       — D1 特征
  data/processed/d2_esm2_features.csv — D2 ESM-2 特征

输出：
  results/fusion_esm2_report.txt
"""

import os
import numpy as np
import pandas as pd
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline

os.makedirs("results", exist_ok=True)

D1_FILE  = "data/processed/features.csv"
D2_FILE  = "data/processed/d2_esm2_features.csv"
OUT_FILE = "results/fusion_esm2_report.txt"


def build_pipeline():
    return Pipeline([
        ("scaler", StandardScaler()),
        ("svm",    SVC(kernel="rbf", C=10, gamma="scale",
                       class_weight="balanced", probability=True,
                       random_state=42)),
    ])


def get_oof_probs(X, y_enc, n_splits=5):
    """
    5 折 out-of-fold 预测概率。
    OOF（Out-Of-Fold）：每一折用其余 4 折训练，
    对这一折预测，拼起来即无泄漏的概率矩阵。
    """
    n_classes = len(np.unique(y_enc))
    oof = np.zeros((len(y_enc), n_classes))
    cv  = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    for train_idx, val_idx in cv.split(X, y_enc):
        clf = build_pipeline()
        clf.fit(X[train_idx], y_enc[train_idx])
        oof[val_idx] = clf.predict_proba(X[val_idx])
    return oof


def main():
    # ── 加载 D1 特征 ─────────────────────────────────────
    d1 = pd.read_csv(D1_FILE)
    d1_drop = [c for c in ["accession", "sequence_id", "host_type"] if c in d1.columns]
    X_d1 = d1.drop(columns=d1_drop).values
    y_d1 = d1["host_type"].values
    print(f"D1 特征：{d1.shape[0]} 个病毒 × {X_d1.shape[1]} 维")

    # ── 加载 D2 ESM-2 特征 ──────────────────────────────
    d2 = pd.read_csv(D2_FILE)
    esm_cols = [c for c in d2.columns if c.startswith("esm_")]
    X_d2 = d2[esm_cols].values
    y_d2 = d2["host_type"].values
    print(f"D2 ESM-2 特征：{d2.shape[0]} 个病毒 × {X_d2.shape[1]} 维")

    # ── 取交集病毒 ──────────────────────────────────────
    # D1 的 sequence_id 格式为 "NC_116874.1_fungi"，去掉末尾 _宿主 后与 D2 对齐
    id_col_d1 = "accession" if "accession" in d1.columns else "sequence_id"
    raw_ids_d1 = d1[id_col_d1].values
    # 去掉最后一个 "_xxx" 后缀（宿主标签），得到纯 accession
    acc_d1 = np.array([s.rsplit("_", 1)[0] if "_" in s else s for s in raw_ids_d1])
    acc_d2 = d2["accession"].values

    common = list(set(acc_d1) & set(acc_d2))
    print(f"两模态共有病毒：{len(common)} 个")

    idx1 = [list(acc_d1).index(a) for a in common]
    idx2 = [list(acc_d2).index(a) for a in common]

    X_d1 = X_d1[idx1]
    X_d2 = X_d2[idx2]
    y    = y_d1[idx1]

    le    = LabelEncoder()
    y_enc = le.fit_transform(y)
    classes = le.classes_
    print(f"宿主类别：{list(classes)}")

    # ── OOF 概率 ─────────────────────────────────────────
    print("\n计算 D1 OOF 概率（5 折）...")
    prob_d1 = get_oof_probs(X_d1, y_enc)

    print("计算 D2 ESM-2 OOF 概率（5 折）...")
    prob_d2 = get_oof_probs(X_d2, y_enc)

    # ── 网格搜索最优融合权重 ─────────────────────────────
    print("\n网格搜索 D1 权重（步长 0.1）...")
    best_w, best_acc = 0.5, 0.0
    for w in np.arange(0.1, 1.0, 0.1):
        prob_fused = w * prob_d1 + (1 - w) * prob_d2
        y_pred     = le.inverse_transform(prob_fused.argmax(axis=1))
        acc        = accuracy_score(y, y_pred)
        print(f"  D1 权重={w:.1f}, D2 权重={(1-w):.1f} → 准确率 {acc*100:.2f}%")
        if acc > best_acc:
            best_acc, best_w = acc, w

    print(f"\n最优权重：D1={best_w:.1f}, D2={1-best_w:.1f}")

    # ── 最终融合结果 ─────────────────────────────────────
    prob_best  = best_w * prob_d1 + (1 - best_w) * prob_d2
    y_pred_best = le.inverse_transform(prob_best.argmax(axis=1))
    acc_best    = accuracy_score(y, y_pred_best)

    print(f"\n── 融合准确率汇总 ──")
    print(f"  D1 单独（k-mer SVM）          : 94.1%")
    print(f"  D2 手工特征 SVM               : 94.0%")
    print(f"  D1+D2 手工融合（原版）        : 95.4%")
    print(f"  D2 ESM-2 单独                 : （见 d2_esm2_report.txt）")
    print(f"  D1+D2-ESM2 融合（新版）       : {acc_best*100:.1f}%")

    lines = [
        f"D1+D2-ESM2 融合准确率: {acc_best:.4f}",
        f"最优权重: D1={best_w:.1f}, D2-ESM2={1-best_w:.1f}",
        "",
        "各权重搜索结果:",
    ]
    for w in np.arange(0.1, 1.0, 0.1):
        prob_fused = w * prob_d1 + (1 - w) * prob_d2
        y_pred     = le.inverse_transform(prob_fused.argmax(axis=1))
        acc        = accuracy_score(y, y_pred)
        lines.append(f"  D1={w:.1f} D2={1-w:.1f}: {acc*100:.2f}%")

    with open(OUT_FILE, "w") as f:
        f.write("\n".join(lines))
    print(f"\n✅ 报告已保存：{OUT_FILE}")


if __name__ == "__main__":
    main()
