# Modelo de Machine Learning

Clasificador RandomForest (scikit-learn) para predicción binaria de necesidad de riego, entrenado con datos sintéticos.

---

## Características del modelo

| Propiedad | Valor |
|---|---|
| Algoritmo | RandomForestClassifier |
| Biblioteca | scikit-learn 1.4+ |
| Licencia | BSD 3-Clause |
| Variables de entrada | temperatura, humedad, pH |
| Salida | Binaria: necesita riego (sí/no) + confianza |
| Datos de entrenamiento | 2000 ejemplos sintéticos |

---

## Variables de entrada

| Variable | Rango | Unidad | Importancia (típica) |
|---|---|---|---|
| `humedad` | 30.0 – 80.0 | % | ~0.58 |
| `temperatura` | 20.0 – 30.0 | °C | ~0.31 |
| `ph` | 5.5 – 7.5 | — | ~0.11 |

---

## Entrenamiento

El modelo se entrena automáticamente al arrancar el procesador. Para ejecutar el entrenamiento de forma independiente:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r src/ml/requirements.txt
python src/ml/train.py
```

**Salida esperada:**

```
[Datos] Generando 2000 ejemplos sintéticos...
[Modelo] Precisión en entrenamiento : 0.974
[Modelo] Precisión en prueba        : 0.967
[Modelo] Importancia de características:
          humedad     : 0.581
          temperatura : 0.312
          ph          : 0.107
[Modelo] Guardado en modelo.pkl
```

El modelo serializado se guarda en `model/model.pkl`. Este archivo **no se versiona** (está en `.gitignore`) porque se regenera con el script de entrenamiento.

---

## Integración con el pipeline

El modelo se usa en dos lugares:

1. **Procesador** (`src/processor/processor.py`) — ejecuta la predicción en cada lectura recibida de NATS JetStream y almacena el resultado en TimescaleDB.
2. **API** (`src/api/main.py`) — endpoint `POST /prediccion` ejecuta el modelo bajo demanda. Ver [api-reference.md](api-reference.md).

---

## Siguiente lectura

- [api-reference.md](api-reference.md) — Endpoint de predicción
- [database.md](database.md) — Cómo se almacenan los resultados
