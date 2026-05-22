"""
使用 SVM 对病毒宿主类型进行分类，评估 D1 特征的预测能力。

SVM（支持向量机）是 GXQ_Create 项目 D1 模块的核心模型。
它擅长处理 k-mer 这类高维稀疏特征，在病毒宿主预测领域已有成熟应用。

输入：data/processed/features.csv
输出：
  results/model_report.txt     — 分类报告（精确率/召回率/F1）
  results/confusion_matrix.csv — 混淆矩阵
  results/feature_importance.csv — 最重要的 k-mer 特征（用 LinearSVC 系数估算）
"""

import os
import pandas as pd
import numpy as np
from sklearn.svm import SVC, LinearSVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import (classification_report, confusion_matrix,
                             accuracy_score)
from sklearn.pipeline import Pipeline

os.makedirs("results", exist_ok=True)

FEATURE_FILE = "data/processed/features.csv"
REPORT_FILE  = "results/model_report.txt"
CM_FILE      = "results/confusion_matrix.csv"
FI_FILE      = "results/feature_importance.csv"


def main():
    # 1. 加载特征表
    df = pd.read_csv(FEATURE_FILE)
    print(f"数据加载完成：{df.shape[0]} 条序列，{df.shape[1]} 列")
    print(f"\n各宿主类型样本数：")
    print(df["host_type"].value_counts().to_string())

    # 2. 分离特征（X）和标签（y）
    # 去掉非特征列，只保留数值特征
    drop_cols = ["sequence_id", "host_type"]
    X = df.drop(columns=drop_cols).values
    y = df["host_type"].values

    # LabelEncoder：将文字标签转成数字（fungi=0, algae=1, bacteria=2 等）
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    class_names = le.classes_
    print(f"\n宿主类别：{list(class_names)}")

    # 3. 构建 SVM 流水线
    # StandardScaler：标准化特征（均值=0，方差=1），SVM 对特征尺度敏感，必须做
    # SVC(kernel='rbf')：使用径向基函数核，适合非线性可分数据
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("svm",    SVC(kernel="rbf", C=10, gamma="scale",
                       class_weight="balanced",   # 处理样本数量不均衡
                       random_state=42)),
    ])

    # 4. 5 折交叉验证
    # 交叉验证：把数据分成 5 份，轮流用 4 份训练、1 份测试，结果更可靠
    print(f"\n正在进行 5 折交叉验证（数据量少时比单次划分更可靠）...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_pred_enc = cross_val_predict(pipeline, X, y_enc, cv=cv)
    y_pred = le.inverse_transform(y_pred_enc)

    # 5. 评估指标
    acc = accuracy_score(y, y_pred)
    report = classification_report(y, y_pred, target_names=class_names)
    cm = confusion_matrix(y, y_pred, labels=class_names)

    print(f"\n── 准确率 ──")
    print(f"  {acc:.4f}  ({acc*100:.1f}%)")
    print(f"\n── 分类报告 ──")
    print(report)

    # 混淆矩阵说明：行=真实标签，列=预测标签，对角线=预测正确的数量
    print(f"── 混淆矩阵 ──")
    cm_df = pd.DataFrame(cm, index=class_names, columns=class_names)
    print(cm_df)

    # 6. 保存报告
    with open(REPORT_FILE, "w") as f:
        f.write(f"准确率: {acc:.4f}\n\n")
        f.write("分类报告:\n")
        f.write(report)
        f.write("\n混淆矩阵（行=真实，列=预测）:\n")
        f.write(cm_df.to_string())
    print(f"\n✅ 分类报告已保存：{REPORT_FILE}")

    cm_df.to_csv(CM_FILE)
    print(f"✅ 混淆矩阵已保存：{CM_FILE}")

    # 7. 用 LinearSVC 估算特征重要性（LinearSVC 有系数，RBF SVC 没有）
    print(f"\n正在计算特征重要性（用 LinearSVC 系数估算）...")
    feature_names = df.drop(columns=drop_cols).columns.tolist()
    lin_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("svm",    LinearSVC(C=1.0, class_weight="balanced",
                             max_iter=2000, random_state=42)),
    ])
    lin_pipe.fit(X, y_enc)

    # 每个特征对各类别的平均绝对系数（越大 = 对分类越重要）
    coef = np.abs(lin_pipe.named_steps["svm"].coef_)
    mean_importance = coef.mean(axis=0)
    fi_df = pd.DataFrame({
        "feature":    feature_names,
        "importance": mean_importance,
    }).sort_values("importance", ascending=False)

    fi_df.to_csv(FI_FILE, index=False)
    print(f"✅ 特征重要性已保存：{FI_FILE}")
    print(f"\n── 最重要的 10 个 k-mer 特征 ──")
    print(fi_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
