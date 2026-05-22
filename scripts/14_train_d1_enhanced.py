"""
使用增强 D1 特征（340 维）训练 SVM，与原版 D1（66 维）对比。

输入：data/processed/d1_enhanced_features.csv
输出：results/d1_enhanced_report.txt
      models/d1_enhanced_pipeline.joblib
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.pipeline import Pipeline

os.makedirs("results", exist_ok=True)
os.makedirs("models",  exist_ok=True)

FEATURE_FILE = "data/processed/d1_enhanced_features.csv"
REPORT_FILE  = "results/d1_enhanced_report.txt"
MODEL_FILE   = "models/d1_enhanced_pipeline.joblib"


def main():
    df = pd.read_csv(FEATURE_FILE)
    print(f"增强 D1 数据加载完成：{df.shape[0]} 条序列，{df.shape[1]} 列")
    print(f"\n各宿主类型样本数：")
    print(df["host_type"].value_counts().to_string())

    drop_cols  = [c for c in ["sequence_id", "host_type"] if c in df.columns]
    feat_cols  = [c for c in df.columns if c not in drop_cols]
    X = df[feat_cols].values.astype(float)
    y = df["host_type"].values

    le    = LabelEncoder()
    y_enc = le.fit_transform(y)
    print(f"\n宿主类别：{list(le.classes_)}")
    print(f"特征维度：{X.shape[1]}")

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("svm",    SVC(kernel="rbf", C=10, gamma="scale",
                       class_weight="balanced", probability=True,
                       random_state=42)),
    ])

    print(f"\n正在进行 5 折交叉验证...")
    cv        = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_pred_enc = cross_val_predict(pipeline, X, y_enc, cv=cv)
    y_pred     = le.inverse_transform(y_pred_enc)

    acc    = accuracy_score(y, y_pred)
    report = classification_report(y, y_pred, target_names=le.classes_)
    cm     = confusion_matrix(y, y_pred, labels=le.classes_)
    cm_df  = pd.DataFrame(cm, index=le.classes_, columns=le.classes_)

    print(f"\n── 增强 D1 准确率 ──")
    print(f"  {acc:.4f}  ({acc*100:.1f}%)")
    print(f"\n── 分类报告 ──")
    print(report)
    print(f"── 混淆矩阵 ──")
    print(cm_df)
    print(f"\n── D1 版本对比 ──")
    print(f"  D1 原版（3-mer，66 维）         : 94.1%")
    print(f"  D1 增强（1+2+3+4-mer，{X.shape[1]} 维）: {acc*100:.1f}%")

    with open(REPORT_FILE, "w") as f:
        f.write(f"D1 增强准确率: {acc:.4f}\n\n")
        f.write(f"特征维度: {X.shape[1]}\n\n")
        f.write("分类报告:\n")
        f.write(report)
        f.write("\n混淆矩阵（行=真实，列=预测）:\n")
        f.write(cm_df.to_string())
    print(f"\n✅ 报告已保存：{REPORT_FILE}")

    pipeline.fit(X, y_enc)
    joblib.dump({"pipeline": pipeline, "label_encoder": le,
                 "feature_cols": feat_cols}, MODEL_FILE)
    print(f"✅ 模型已保存：{MODEL_FILE}")


if __name__ == "__main__":
    main()
