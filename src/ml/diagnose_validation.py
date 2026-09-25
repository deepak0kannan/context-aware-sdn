#!/usr/bin/env python3
"""
Diagnostic Script: Evaluates ML generalization with and without duration features.
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

df_train = pd.read_csv("/home/deeepo/sdn_project/data/sdn_dataset_large.csv")
df_ext = pd.read_csv("/home/deeepo/sdn_project/data/sdn_dataset_external.csv")

le = LabelEncoder()
y_train = le.fit_transform(df_train['label'])
y_ext = le.transform(df_ext['label'])
classes = list(le.classes_)

# 1. With All 10 Features (including flow_duration_sec)
feats_all = [
    'packet_rate', 'byte_rate', 'flow_duration_sec', 'ip_src_count',
    'ip_src_entropy', 'avg_packet_size', 'std_packet_size',
    'port_status', 'rx_dropped', 'tx_dropped'
]

# 2. Pure Telemetry (Excluding flow_duration_sec)
feats_pure = [
    'packet_rate', 'byte_rate', 'ip_src_count',
    'ip_src_entropy', 'avg_packet_size', 'std_packet_size',
    'port_status', 'rx_dropped', 'tx_dropped'
]

print("=" * 70)
print(f"DIAGNOSING GENERALIZATION ON EXTERNAL UNSEEN DATASET ({len(df_ext)} samples)")
print("=" * 70)

for name, feat_list in [("WITH flow_duration_sec (10 feats)", feats_all), ("WITHOUT flow_duration_sec (9 feats)", feats_pure)]:
    print(f"\n--- Feature Set: {name} ---")
    X_tr = df_train[feat_list].fillna(0)
    X_te = df_ext[feat_list].fillna(0)

    for m_name, model in [
        ("Random Forest", RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)),
        ("Gradient Boosting", GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42))
    ]:
        cv = cross_val_score(model, X_tr, y_train, cv=10, scoring='accuracy')
        model.fit(X_tr, y_train)
        preds = model.predict(X_te)
        acc = accuracy_score(y_ext, preds)
        print(f"  {m_name:20s} | 10-Fold CV: {cv.mean()*100:5.2f}% (+/- {cv.std()*100:4.2f}%) | External Test Acc: {acc*100:5.2f}%")
        if "WITHOUT" in name and m_name == "Gradient Boosting":
            print("\nConfusion Matrix (Gradient Boosting without duration):")
            cm = confusion_matrix(y_ext, preds)
            header = f"{'':16s}" + "".join(f"{c[:10]:>12s}" for c in classes)
            print(header)
            for i, c in enumerate(classes):
                print(f"{c:16s}" + "".join(f"{cm[i][j]:12d}" for j in range(len(classes))))
            print("\nClassification Report:")
            print(classification_report(y_ext, preds, target_names=classes))
