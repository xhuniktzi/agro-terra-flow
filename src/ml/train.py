#!/usr/bin/env python3

import argparse
import pickle

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


def generar_datos(n: int = 2_000, seed: int = 42) -> tuple:
    rng = np.random.default_rng(seed)

    temperatura = rng.uniform(15.0, 38.0, n)
    humedad = rng.uniform(15.0, 95.0, n)
    ph = rng.uniform(5.0, 8.0, n)

    y = ((humedad < 40) | ((humedad < 60) & (temperatura > 28))).astype(int)

    idx_ruido = rng.choice(n, size=int(n * 0.05), replace=False)
    y[idx_ruido] = 1 - y[idx_ruido]

    X = np.column_stack([temperatura, humedad, ph])
    return X, y


def entrenar(X, y) -> RandomForestClassifier:
    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    clf.fit(X, y)
    return clf


def main():
    parser = argparse.ArgumentParser(description="Entrena el modelo de riego")
    parser.add_argument("--output", default="modelo.pkl")
    parser.add_argument("--n-samples", type=int, default=2_000)
    args = parser.parse_args()

    print(f"[Datos] Generando {args.n_samples} ejemplos sintéticos...")
    X, y = generar_datos(n=args.n_samples)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("[Modelo] Entrenando RandomForestClassifier (100 árboles)...")
    clf = entrenar(X_train, y_train)

    acc_train = clf.score(X_train, y_train)
    acc_test = clf.score(X_test, y_test)

    print(f"[Modelo] Precisión en entrenamiento : {acc_train:.3f}")
    print(f"[Modelo] Precisión en prueba        : {acc_test:.3f}")

    n_no_riego = int((y == 0).sum())
    n_riego = int((y == 1).sum())
    print("[Modelo] Distribución de etiquetas:")
    print(f"          No riego  : {n_no_riego:4d} ({100*n_no_riego/len(y):.1f}%)")
    print(f"          Riego     : {n_riego:4d} ({100*n_riego/len(y):.1f}%)")

    features = ["temperatura", "humedad", "ph"]
    importancias = clf.feature_importances_
    print("[Modelo] Importancia de características:")
    for feat, imp in sorted(zip(features, importancias), key=lambda x: -x[1]):
        print(f"          {feat:<12}: {imp:.3f}")

    print("\n[Modelo] Reporte de clasificación (conjunto de prueba):")
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=["No riego", "Riego"]))

    with open(args.output, "wb") as f:
        pickle.dump(clf, f)
    print(f"[Modelo] Guardado en {args.output}")


if __name__ == "__main__":
    main()
