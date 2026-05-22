"""
使用 SVM 对 D2 蛋白质特征进行宿主分类，与 D1 结果对比。

输入：data/processed/d2_features.csv
输出：results/d2_model_report.txt、results/d2_confusion_matrix.csv
"""

import os
import pandas as pd
import numpy as np
from sklearn.svm import SVC, LinearSVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.pipeline import Pipeline

os.makedirs("results", exist_ok=True)

FEATURE_FILE = "data/processed/d2_features.csv"
REPORT_FILE  = "results/d2_model_report.txt"
CM_FILE      = "results/d2_confusion_matrix.csv"


def main():
    df = pd.read_csv(FEATURE_FILE)
    print(f"D2 数据加载完成：{df.shape[0]} 条病毒，{df.shape[1]} 列")
    print(f"\n各宿主类型样本数：")
    print(df["host_type"].value_counts().to_string())

    drop_cols = ["accession", "host_type"]
    X = df.drop(columns=drop_cols).values
    y = df["host_type"].values

    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    class_names = le.classes_
    print(f"\n宿主类别：{list(class_names)}")
    print(f"特征维度：{X.shape[1]}")

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("svm",    SVC(kernel="rbf", C=10, gamma="scale",
                       class_weight="balanced", random_state=42)),
    ])

    print(f"\n正在进行 5 折交叉验证...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_pred_enc = cross_val_predict(pipeline, X, y_enc, cv=cv)
    y_pred = le.inverse_transform(y_pred_enc)

    acc = accuracy_score(y, y_pred)
    report = classification_report(y, y_pred, target_names=class_names)
    cm = confusion_matrix(y, y_pred, labels=class_names)
    cm_df = pd.DataFrame(cm, index=class_names, columns=class_names)

    print(f"\n── D2 准确率 ──")
    print(f"  {acc:.4f}  ({acc*100:.1f}%)")
    print(f"\n── 分类报告 ──")
    print(report)
    print(f"── 混淆矩阵 ──")
    print(cm_df)

    # D1 vs D2 对比
    print(f"\n── D1 vs D2 对比 ──")
    print(f"  D1（k-mer 序列特征）  : 94.1%")
    print(f"  D2（蛋白质理化特征）  : {acc*100:.1f}%")

    with open(REPORT_FILE, "w") as f:
        f.write(f"D2 准确率: {acc:.4f}\n\n")
        f.write("分类报告:\n")
        f.write(report)
        f.write("\n混淆矩阵（行=真实，列=预测）:\n")
        f.write(cm_df.to_string())

    cm_df.to_csv(CM_FILE)
    print(f"\n✅ D2 报告已保存：{REPORT_FILE}")


if __name__ == "__main__":
    main()
