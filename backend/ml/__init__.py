"""Velaris Module 1 — Jewelry Type Classification (CNN, transfer learning).

This package holds the production inference wrapper only. Training code
lives in ml_training/ at the repo root, kept separate so the deployed
backend doesn't need training-only dependencies (huggingface_hub,
scikit-learn, matplotlib) installed on the server.
"""
