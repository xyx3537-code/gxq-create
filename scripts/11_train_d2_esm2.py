"""
使用 ESM-2 特征训练 D2 宿主分类 SVM，与手工特征版本对比。

输入：data/processed/d2_esm2_features.csv
输出：results/d2_esm2_report.txt
      results/d2_esm2_confusion_matrix.csv
      models/d2_esm2_pipeline.joblib
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

FEATURE_FILE = "data/processed/d2_esm2_features.csv"
REPORT_FILE  = "results/d2_esm2_report.txt"
CM_FILE      = "results/d2_esm2_confusion_matrix.csv"
MODEL_FILE   = "models/d2_esm2_pipeline.joblib"


def main():
    df = pd.read_csv(FEATURE_FILE)
    print(f"ESM-2 D2 数据加载完成：{df.shape[0]} 条病毒，{df.shape[1]} 列")
    print(f"\n各宿主类型样本数：")
    print(df["host_type"].value_counts().to_string())

    feature_cols = [c for c in df.columns if c.startswith("esm_")]
    X = df[feature_cols].values
    y = df["host_type"].values

    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    class_names = le.classes_
    print(f"\n宿主类别：{list(class_names)}")
    print(f"特征维度：{X.shape[1]}（ESM-2 320 维 embedding）")

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("svm",    SVC(kernel="rbf", C=10, gamma="scale",
                       class_weight="balanced", probability=True,
                       random_state=42)),
    ])

    print(f"\n正在进行 5 折交叉验证（320 维特征，稍慢）...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_pred_enc = cross_val_predict(pipeline, X, y_enc, cv=cv)
    y_pred     = le.inverse_transform(y_pred_enc)

    acc    = accuracy_score(y, y_pred)
    report = classification_report(y, y_pred, target_names=class_names)
    cm     = confusion_matrix(y, y_pred, labels=class_names)
    cm_df  = pd.DataFrame(cm, index=class_names, columns=class_names)

    print(f"\n── D2 ESM-2 准确率 ──")
    print(f"  {acc:.4f}  ({acc*100:.1f}%)")
    print(f"\n── 分类报告 ──")
    print(report)
    print(f"── 混淆矩阵 ──")
    print(cm_df)

    print(f"\n── 特征版本对比 ──")
    print(f"  D2 手工特征（27 维理化） : 94.0%")
    print(f"  D2 ESM-2 embedding（320 维）: {acc*100:.1f}%")

    with open(REPORT_FILE, "w") as f:
        f.write(f"D2 ESM-2 准确率: {acc:.4f}\n\n")
        f.write("分类报告:\n")
        f.write(report)
        f.write("\n混淆矩阵（行=真实，列=预测）:\n")
        f.write(cm_df.to_string())
    print(f"\n✅ 报告已保存：{REPORT_FILE}")

    # 在全量数据上重新拟合，保存完整模型
    pipeline.fit(X, y_enc)
    joblib.dump({"pipeline": pipeline, "label_encoder": le}, MODEL_FILE)
    print(f"✅ 模型已保存：{MODEL_FILE}")


if __name__ == "__main__":
    main()
