#!/usr/bin/env python3
import joblib
import sys

print(f"Python Version: {sys.version}")
try:
    model = joblib.load("/home/deeepo/sdn_project/models/sdn_classifier.joblib")
    print(f"SUCCESS: Model loaded! Type: {type(model).__name__}")
    print(f"Features expected: {model.n_features_in_}")
    print(f"Classes: {model.classes_}")
except Exception as e:
    print(f"ERROR loading model: {e}")
