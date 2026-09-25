#!/usr/bin/env python3
"""
Phase 5b: Comprehensive Cross-Validation & Multi-Model Benchmarking
Performs rigorous 10-Fold Stratified Cross-Validation across multiple ML algorithms:
- Gradient Boosting Classifier
- Random Forest Classifier
- Decision Tree Baseline
- K-Nearest Neighbors (KNN)

Evaluates:
- 10-Fold CV Accuracy & 95% Confidence Interval
- Generalization Gap (Train vs. Validation score)
- Macro Precision, Recall, and F1-Score
- Out-of-Fold (OOF) Confusion Matrix
- Per-Class Reliability Analysis
- Feature Importance Ranking
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)


def run_cross_validation(dataset_path=None, output_dir=None):
    if dataset_path is None:
        dataset_path = os.path.expanduser("~/sdn_project/data/sdn_dataset_large.csv")
        if not os.path.exists(dataset_path):
            dataset_path = os.path.expanduser("~/sdn_project/data/sdn_dataset.csv")

    if output_dir is None:
        output_dir = os.path.expanduser("~/sdn_project/models")

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("      COMPREHENSIVE 10-FOLD STRATIFIED CROSS-VALIDATION      ")
    print("=" * 70)
    print(f"[*] Dataset: {dataset_path}")

    if not os.path.exists(dataset_path):
        print(f"[!] Error: Dataset file not found at {dataset_path}")
        sys.exit(1)

    df = pd.read_csv(dataset_path)
    print(f"[*] Total dataset instances : {len(df)}")
    print(f"[*] Feature columns count   : {df.shape[1] - 1}")
    print("\n[*] Ground-Truth Class Distribution:")
    counts = df['label'].value_counts()
    for lbl, cnt in counts.items():
        print(f"    - {lbl:16s}: {cnt:4d} samples ({cnt/len(df)*100:5.1f}%)")

    # Features and labels (pure network telemetry)
    feature_cols = [
        'packet_rate', 'byte_rate', 'ip_src_count',
        'ip_src_entropy', 'avg_packet_size', 'std_packet_size',
        'port_status', 'rx_dropped', 'tx_dropped'
    ]

    X = df[feature_cols].copy().replace([np.inf, -np.inf], np.nan).fillna(0)
    y_raw = df['label'].values

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_raw)
    class_names = list(label_encoder.classes_)

    # 10-Fold Stratified K-Fold
    kfold = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)

    # Candidate Models to Benchmark
    models = {
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
        "Decision Tree": DecisionTreeClassifier(max_depth=8, random_state=42),
        "K-Nearest Neighbors": Pipeline([("scaler", StandardScaler()), ("knn", KNeighborsClassifier(n_neighbors=5))])
    }

    results = {}
    print("\n" + "=" * 70)
    print(" 1. BENCHMARKING MULTIPLE ARCHITECTURES VIA 10-FOLD CV")
    print("=" * 70)
    print(f"{'Model Name':22s} | {'CV Mean Acc':11s} | {'Std Dev':8s} | {'95% Conf. Interval':20s} | {'Gen. Gap':9s}")
    print("-" * 80)

    champion_name = None
    champion_score = -1.0
    champion_model = None

    for name, model in models.items():
        scoring = {'accuracy': 'accuracy', 'f1_macro': 'f1_macro', 'precision_macro': 'precision_macro', 'recall_macro': 'recall_macro'}
        cv_res = cross_validate(model, X, y, cv=kfold, scoring=scoring, return_train_score=True)

        val_acc_mean = cv_res['test_accuracy'].mean()
        val_acc_std = cv_res['test_accuracy'].std()
        train_acc_mean = cv_res['train_accuracy'].mean()
        gen_gap = train_acc_mean - val_acc_mean  # Overfitting measure

        # 95% Confidence Interval: mean +/- 1.96 * (std / sqrt(K))
        ci_margin = 1.96 * (val_acc_std / np.sqrt(10))
        ci_str = f"[{val_acc_mean - ci_margin:.4f}, {min(1.0, val_acc_mean + ci_margin):.4f}]"

        results[name] = {
            "cv_accuracy_mean": float(val_acc_mean),
            "cv_accuracy_std": float(val_acc_std),
            "train_accuracy_mean": float(train_acc_mean),
            "generalization_gap": float(gen_gap),
            "f1_macro_mean": float(cv_res['test_f1_macro'].mean()),
            "precision_macro_mean": float(cv_res['test_precision_macro'].mean()),
            "recall_macro_mean": float(cv_res['test_recall_macro'].mean()),
            "confidence_interval_95": [float(val_acc_mean - ci_margin), float(min(1.0, val_acc_mean + ci_margin))]
        }

        print(f"{name:22s} | {val_acc_mean*100:6.2f}%    | +/-{val_acc_std*100:4.2f}% | {ci_str:20s} | {gen_gap*100:5.2f}%")

        if val_acc_mean > champion_score:
            champion_score = val_acc_mean
            champion_name = name
            champion_model = model

    print("=" * 80)
    print(f"[*] CHAMPION ARCHITECTURE: {champion_name.upper()} ({champion_score*100:.2f}% CV ACCURACY)")
    print("=" * 80)

    # 2. Out-of-Fold (OOF) Prediction Matrix for Champion Model
    print(f"\n[*] Generating Out-Of-Fold (OOF) Predictions with {champion_name}...")
    oof_predictions = np.zeros(len(y), dtype=int)
    fold_accuracies = []

    for fold_idx, (train_idx, val_idx) in enumerate(kfold.split(X, y)):
        X_tr, y_tr = X.iloc[train_idx], y[train_idx]
        X_va, y_va = X.iloc[val_idx], y[val_idx]

        model_clone = Pipeline([("scaler", StandardScaler()), ("knn", KNeighborsClassifier(n_neighbors=5))]) if champion_name == "K-Nearest Neighbors" else type(champion_model)(**champion_model.get_params())
        model_clone.fit(X_tr, y_tr)
        preds = model_clone.predict(X_va)
        oof_predictions[val_idx] = preds
        fold_acc = accuracy_score(y_va, preds)
        fold_accuracies.append(fold_acc)

    print("\n" + "=" * 70)
    print(" 2. OUT-OF-FOLD COMPREHENSIVE CLASSIFICATION REPORT")
    print("=" * 70)
    print(classification_report(y, oof_predictions, target_names=class_names, digits=4))

    print("\n" + "=" * 70)
    print(" 3. OUT-OF-FOLD AGGREGATE CONFUSION MATRIX")
    print("=" * 70)
    cm = confusion_matrix(y, oof_predictions)
    cm_df = pd.DataFrame(cm, index=[f"True: {c}" for c in class_names], columns=[f"Pred: {c}" for c in class_names])
    print(cm_df)

    # 3. Train final model on 100% of data for production deployment
    print(f"\n[*] Fitting final production model ({champion_name}) on full dataset...")
    champion_model.fit(X, y)

    # Feature Importances (for tree-based models)
    if hasattr(champion_model, "feature_importances_"):
        print("\n" + "=" * 70)
        print(" 4. FEATURE IMPORTANCE RANKING")
        print("=" * 70)
        importances = pd.Series(champion_model.feature_importances_, index=feature_cols).sort_values(ascending=False)
        for col, imp in importances.items():
            bar = "#" * int(imp * 40)
            print(f"  {col:18s} | {imp*100:5.1f}% | {bar}")

    # Save artifacts
    model_path = os.path.join(output_dir, "sdn_classifier.joblib")
    joblib.dump(champion_model, model_path)
    print(f"\n[*] Production model saved to: {model_path}")

    report_data = {
        "dataset_size": len(df),
        "class_distribution": counts.to_dict(),
        "cross_validation_k": 10,
        "champion_model": champion_name,
        "champion_cv_accuracy": float(champion_score),
        "all_model_results": results,
        "confusion_matrix": cm.tolist(),
        "classes": class_names,
        "features": feature_cols
    }

    report_path = os.path.join(output_dir, "cross_validation_report.json")
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)
    print(f"[*] Cross-validation report saved to: {report_path}")

    print("\n=======================================================")
    print("         CROSS-VALIDATION EXPERIMENT COMPLETED         ")
    print("=======================================================\n")
    return report_data


if __name__ == "__main__":
    ds = sys.argv[1] if len(sys.argv) > 1 else None
    run_cross_validation(dataset_path=ds)
