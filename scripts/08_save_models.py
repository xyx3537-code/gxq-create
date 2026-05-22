"""
用全量数据训练最终模型并序列化保存，供预测脚本和 Flask API 调用。

保存文件（models/ 目录）：
  d1_pipeline.joblib   — D1 SVM pipeline（StandardScaler + SVC）
  d2_pipeline.joblib   — D2 ESM-2 SVM pipeline（StandardScaler + SVC）
  label_encoder.joblib — 宿主类别编码器（动态，当前 6 类）
  fusion_weight.json   — 最优融合权重 {w_d1, w_d2}
  feature_meta.json    — D1/D2 特征列名，预测时对齐用
"""

import re
import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline

os.makedirs("models", exist_ok=True)

D1_FILE = "data/processed/features.csv"
D2_FILE = "data/processed/d2_esm2_features.csv"  # 使用 ESM-2 特征

FUSION_W_D1 = 0.40   # 12 号脚本网格搜索得到的最优权重（D1+D2-ESM2）


def make_strip_fn(host_types):
    pattern = re.compile(r'_(' + '|'.join(host_types) + r')$')
    return lambda seq_id: pattern.sub('', seq_id)


def make_pipeline():
    return Pipeline([
        ("scaler", StandardScaler()),
        ("svm",   SVC(kernel="rbf", C=10, gamma="scale",
                      class_weight="balanced", probability=True,
                      random_state=42)),
    ])


def main():
    # ── 1. 加载并对齐数据（与 12 号脚本逻辑一致）──────────
    d1 = pd.read_csv(D1_FILE)
    d2 = pd.read_csv(D2_FILE)

    strip_host_suffix = make_strip_fn(d1["host_type"].unique().tolist())
    d1["accession"] = d1["sequence_id"].apply(strip_host_suffix)
    common = set(d1["accession"]) & set(d2["accession"])

    d2_label = dict(zip(d2["accession"], d2["host_type"]))
    d1 = d1[d1.apply(lambda r: d2_label.get(r["accession"]) == r["host_type"], axis=1)]
    d1 = d1[d1["accession"].isin(common)].sort_values("accession").reset_index(drop=True)
    d2 = d2[d2["accession"].isin(common)].sort_values("accession").reset_index(drop=True)

    print(f"训练样本数：{len(d1)} 条病毒，{len(set(d1['host_type']))} 类宿主")
    print(d1["host_type"].value_counts().to_string())

    # ── 2. 准备特征矩阵和标签 ─────────────────────────────
    drop_d1 = ["sequence_id", "host_type", "accession"]
    drop_d2 = ["accession", "host_type"]
    d1_feat_cols = [c for c in d1.columns if c not in drop_d1]
    d2_feat_cols = [c for c in d2.columns if c not in drop_d2]

    X1 = d1[d1_feat_cols].values.astype(float)
    X2 = d2[d2_feat_cols].values.astype(float)
    y  = d1["host_type"].values

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # ── 3. 用全量数据训练最终模型 ─────────────────────────
    print("\n训练 D1 模型（全量）...")
    clf_d1 = make_pipeline()
    clf_d1.fit(X1, y_enc)

    print("训练 D2 模型（全量）...")
    clf_d2 = make_pipeline()
    clf_d2.fit(X2, y_enc)

    # ── 4. 保存模型和元数据 ───────────────────────────────
    joblib.dump(clf_d1, "models/d1_pipeline.joblib")
    joblib.dump(clf_d2, "models/d2_pipeline.joblib")
    joblib.dump(le,     "models/label_encoder.joblib")
    # d2_esm2_pipeline.joblib 已由 11 号脚本保存，这里不重复保存

    with open("models/fusion_weight.json", "w") as f:
        json.dump({"w_d1": FUSION_W_D1, "w_d2": round(1 - FUSION_W_D1, 2)}, f, indent=2)

    with open("models/feature_meta.json", "w") as f:
        json.dump({"d1_features": d1_feat_cols,
                   "d2_features": d2_feat_cols,
                   "host_types":  list(le.classes_)}, f, indent=2, ensure_ascii=False)

    print("\n✅ 模型已保存：")
    for fname in ["d1_pipeline.joblib", "d2_pipeline.joblib",
                  "label_encoder.joblib", "fusion_weight.json", "feature_meta.json"]:
        size = os.path.getsize(f"models/{fname}")
        print(f"  models/{fname}  ({size/1024:.1f} KB)")

    # ── 5. 快速验证：在训练集上预测，检查是否正常加载 ────
    clf_d1_loaded = joblib.load("models/d1_pipeline.joblib")
    clf_d2_loaded = joblib.load("models/d2_pipeline.joblib")
    le_loaded     = joblib.load("models/label_encoder.joblib")

    p1 = clf_d1_loaded.predict_proba(X1)
    p2 = clf_d2_loaded.predict_proba(X2)
    p_fused = FUSION_W_D1 * p1 + (1 - FUSION_W_D1) * p2
    y_pred = le_loaded.inverse_transform(p_fused.argmax(axis=1))

    from sklearn.metrics import accuracy_score
    acc = accuracy_score(y, y_pred)
    print(f"\n加载验证（训练集自测，仅检查模型是否正常）：{acc*100:.1f}%")
    print("（注：训练集自测不等于泛化准确率，泛化准确率见 results/fusion_report.txt）")


if __name__ == "__main__":
    main()
