#!/usr/bin/env python3
"""
Phase 5: Machine Learning Anomaly Classifier Training & Evaluation
Trains Random Forest and Gradient Boosting multi-class classifiers to discriminate
between:
- normal
- flash_crowd
- ddos
- slow_congestion
- link_failure

Outputs:
- 5-Fold Cross-Validation Accuracy
- Confusion Matrix & Classification Report
- Feature Importance ranking
- Serialized Model: models/sdn_classifier.joblib
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import LabelEncoder


def train_and_evaluate(dataset_path=None, model_dir=None):
    if dataset_path is None:
        dataset_path = os.path.expanduser("~/sdn_project/data/sdn_dataset.csv")
    if model_dir is None:
        model_dir = os.path.expanduser("~/sdn_project/models")

    os.makedirs(model_dir, exist_ok=True)

    print(f"[*] Loading dataset from: {dataset_path}")
    if not os.path.exists(dataset_path):
        print(f"[ERROR] Dataset not found at: {dataset_path}")
        sys.exit(1)

    df = pd.read_csv(dataset_path)
    print(f"[*] Total dataset shape: {df.shape}")
    print("[*] Class distribution:")
    print(df['label'].value_counts())
    print("=" * 60)

    # Feature selection: pure network telemetry (no temporal leakage)
    feature_cols = [
        'packet_rate', 'byte_rate', 'ip_src_count',
        'ip_src_entropy', 'avg_packet_size', 'std_packet_size',
        'port_status', 'rx_dropped', 'tx_dropped'
    ]

    # Clean missing/infinite values
    X = df[feature_cols].copy()
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0)
    y_raw = df['label'].values

    # Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_raw)
    class_names = list(label_encoder.classes_)

    # Stratified Train/Test split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"[*] Training samples: {len(X_train)} | Test samples: {len(X_test)}")
    print("=" * 60)

    # 1. Random Forest Classifier
    print("[*] Training Random Forest Classifier...")
    rf_model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    rf_cv_scores = cross_val_score(rf_model, X_train, y_train, cv=cv, scoring='accuracy')
    print(f"[RF] 5-Fold Cross-Validation Accuracy: {rf_cv_scores.mean():.4f} (+/- {rf_cv_scores.std():.4f})")

    rf_model.fit(X_train, y_train)
    rf_preds = rf_model.predict(X_test)
    rf_acc = accuracy_score(y_test, rf_preds)
    print(f"[RF] Test Set Accuracy: {rf_acc * 100:.2f}%\n")

    # 2. Gradient Boosting Classifier
    print("[*] Training Gradient Boosting Classifier...")
    gb_model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42)
    gb_cv_scores = cross_val_score(gb_model, X_train, y_train, cv=cv, scoring='accuracy')
    print(f"[GB] 5-Fold Cross-Validation Accuracy: {gb_cv_scores.mean():.4f} (+/- {gb_cv_scores.std():.4f})")

    gb_model.fit(X_train, y_train)
    gb_preds = gb_model.predict(X_test)
    gb_acc = accuracy_score(y_test, gb_preds)
    print(f"[GB] Test Set Accuracy: {gb_acc * 100:.2f}%\n")

    # Choose champion model
    best_model = rf_model if rf_acc >= gb_acc else gb_model
    best_name = "RandomForest" if best_model == rf_model else "GradientBoosting"
    best_preds = rf_preds if best_model == rf_model else gb_preds

    print("=" * 60)
    print(f"[*] CHAMPION MODEL SELECTED: {best_name.upper()}")
    print("=" * 60)
    print("\n[+] Classification Report:")
    print(classification_report(y_test, best_preds, target_names=class_names, digits=4))

    print("\n[+] Confusion Matrix:")
    cm = confusion_matrix(y_test, best_preds)
    cm_df = pd.DataFrame(cm, index=class_names, columns=class_names)
    print(cm_df)

    # Feature importances
    if hasattr(best_model, "feature_importances_"):
        print("\n[+] Feature Importances:")
        importances = pd.Series(best_model.feature_importances_, index=feature_cols).sort_values(ascending=False)
        for col, imp in importances.items():
            print(f"  - {col:18s}: {imp:.4f} ({imp*100:.1f}%)")

    # Save artifacts
    model_save_path = os.path.join(model_dir, "sdn_classifier.joblib")
    joblib.dump(best_model, model_save_path)
    print(f"\n[*] Serialized model saved to: {model_save_path}")

    metadata = {
        "model_type": best_name,
        "features": feature_cols,
        "classes": class_names,
        "accuracy": float(accuracy_score(y_test, best_preds)),
        "cv_accuracy_mean": float(rf_cv_scores.mean() if best_name == "RandomForest" else gb_cv_scores.mean()),
        "cv_accuracy_std": float(rf_cv_scores.std() if best_name == "RandomForest" else gb_cv_scores.std())
    }

    metadata_path = os.path.join(model_dir, "model_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"[*] Model metadata saved to: {metadata_path}")
    print("\n=========================================")
    print("        PHASE 5 TRAINING: COMPLETE        ")
    print("=========================================\n")


if __name__ == "__main__":
    ds_path = sys.argv[1] if len(sys.argv) > 1 else None
    train_and_evaluate(dataset_path=ds_path)
