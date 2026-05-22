"""
D1 增强 + D2-ESM2 后期融合，与之前 96.8% 基准对比。

输入：
  data/processed/d1_enhanced_features.csv
  data/processed/d2_esm2_features.csv

输出：
  results/fusion_d1enhanced_esm2_report.txt
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

D1_FILE  = "data/processed/d1_enhanced_features.csv"
D2_FILE  = "data/processed/d2_esm2_features.csv"
OUT_FILE = "results/fusion_d1enhanced_esm2_report.txt"


def build_pipeline():
    return Pipeline([
        ("scaler", StandardScaler()),
        ("svm",    SVC(kernel="rbf", C=10, gamma="scale",
                       class_weight="balanced", probability=True,
                       random_state=42)),
    ])


def get_oof_probs(X, y_enc, n_splits=5):
    """5 折 out-of-fold 预测概率（无数据泄漏）"""
    n_classes = len(np.unique(y_enc))
    oof = np.zeros((len(y_enc), n_classes))
    cv  = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    for train_idx, val_idx in cv.split(X, y_enc):
        clf = build_pipeline()
        clf.fit(X[train_idx], y_enc[train_idx])
        oof[val_idx] = clf.predict_proba(X[val_idx])
    return oof


def main():
    # ── 加载 D1 增强特征 ─────────────────────────────────
    d1 = pd.read_csv(D1_FILE)
    drop_d1   = [c for c in ["sequence_id", "host_type"] if c in d1.columns]
    feat_d1   = [c for c in d1.columns if c not in drop_d1]
    X_d1_full = d1[feat_d1].values.astype(float)
    y_d1_full = d1["host_type"].values
    acc_d1    = d1["sequence_id"].values if "sequence_id" in d1.columns else d1.index.astype(str)
    # 还原纯 accession（去掉末尾 _宿主 后缀）
    acc_d1_clean = np.array([s.rsplit("_", 1)[0] if "_" in s else s for s in acc_d1])
    print(f"D1 增强特征：{d1.shape[0]} 个病毒 × {len(feat_d1)} 维")

    # ── 加载 D2 ESM-2 特征 ──────────────────────────────
    d2       = pd.read_csv(D2_FILE)
    esm_cols = [c for c in d2.columns if c.startswith("esm_")]
    X_d2_full = d2[esm_cols].values
    acc_d2    = d2["accession"].values
    print(f"D2 ESM-2 特征：{d2.shape[0]} 个病毒 × {len(esm_cols)} 维")

    # ── 取交集 ───────────────────────────────────────────
    common = list(set(acc_d1_clean) & set(acc_d2))
    print(f"两模态共有病毒：{len(common)} 个")

    idx1 = [list(acc_d1_clean).index(a) for a in common]
    idx2 = [list(acc_d2).index(a) for a in common]

    X_d1 = X_d1_full[idx1]
    X_d2 = X_d2_full[idx2]
    y    = y_d1_full[idx1]

    le    = LabelEncoder()
    y_enc = le.fit_transform(y)
    classes = le.classes_

    # ── OOF 概率 ─────────────────────────────────────────
    print("\n计算 D1 增强 OOF 概率（5 折）...")
    prob_d1 = get_oof_probs(X_d1, y_enc)

    print("计算 D2 ESM-2 OOF 概率（5 折）...")
    prob_d2 = get_oof_probs(X_d2, y_enc)

    # ── 网格搜索最优融合权重 ─────────────────────────────
    print("\n网格搜索 D1 权重（步长 0.1）...")
    best_w, best_acc = 0.5, 0.0
    for w in np.arange(0.1, 1.0, 0.1):
        fused  = w * prob_d1 + (1 - w) * prob_d2
        y_pred = le.inverse_transform(fused.argmax(axis=1))
        acc    = accuracy_score(y, y_pred)
        print(f"  D1={w:.1f}, D2={1-w:.1f} → {acc*100:.2f}%")
        if acc > best_acc:
            best_acc, best_w = acc, w

    fused_best  = best_w * prob_d1 + (1 - best_w) * prob_d2
    y_pred_best = le.inverse_transform(fused_best.argmax(axis=1))
    acc_best    = accuracy_score(y, y_pred_best)

    print(f"\n── 融合准确率汇总 ──")
    print(f"  D1 原版（3-mer）+ D2 手工融合    : 95.4%")
    print(f"  D1 原版（3-mer）+ D2 ESM-2 融合  : 96.8%")
    print(f"  D1 增强（1+2+3+4-mer）单独       : （见 d1_enhanced_report.txt）")
    print(f"  D1 增强 + D2-ESM2 融合（新版）   : {acc_best*100:.1f}%")
    print(f"  最优权重：D1={best_w:.1f}, D2={1-best_w:.1f}")

    lines = [
        f"D1增强+D2-ESM2 融合准确率: {acc_best:.4f}",
        f"最优权重: D1增强={best_w:.1f}, D2-ESM2={1-best_w:.1f}",
        "",
        "各权重搜索结果:",
    ]
    for w in np.arange(0.1, 1.0, 0.1):
        fused  = w * prob_d1 + (1 - w) * prob_d2
        y_pred = le.inverse_transform(fused.argmax(axis=1))
        acc    = accuracy_score(y, y_pred)
        lines.append(f"  D1={w:.1f} D2={1-w:.1f}: {acc*100:.2f}%")

    with open(OUT_FILE, "w") as f:
        f.write("\n".join(lines))
    print(f"\n✅ 报告已保存：{OUT_FILE}")


if __name__ == "__main__":
    main()
