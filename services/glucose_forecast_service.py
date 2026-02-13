# services/glucose_forecast_service.py
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import tensorflow as tf
import keras


@dataclass(frozen=True)
class ForecastConfig:
    freq_min: int
    lookback: int
    offsets: List[int]  
    target: str = "glucose"
    units: str = "mg/dL"


@dataclass(frozen=True)
class ForecastPoint:
    timestamp: datetime
    value_mg_dl: float
    ahead_min: int


@dataclass(frozen=True)
class ForecastOutput:
    anchor_time: datetime
    config: ForecastConfig
    predicted: List[ForecastPoint]


class GlucoseForecastService:
    """
    Serviço responsável por:
      - carregar model (.keras) + scaler (.joblib) + meta (.json) de services/artifacts/
      - preparar input (1, CTX, 1) com StandardScaler no eixo da feature
      - rodar predict e devolver pontos previstos em mg/dL para os OFFSETS
    """

    _model: Optional[tf.keras.Model] = None
    _scaler: Any = None
    _config: Optional[ForecastConfig] = None

    def __init__(
        self,
        artifacts_dir: Optional[str] = None,
    ) -> None:
        self._artifacts_dir = Path(artifacts_dir) if artifacts_dir else (Path(__file__).resolve().parent / "artifacts")

        self._model_path = self._artifacts_dir / "shanghai_lstm_v1.keras"
        self._scaler_path = self._artifacts_dir / "shanghai_scaler_v1.joblib"
        self._meta_path = self._artifacts_dir / "shanghai_model_v1.json"

    def _load_config(self) -> ForecastConfig:
        if GlucoseForecastService._config is not None:
            return GlucoseForecastService._config

        if not self._meta_path.exists():
            raise FileNotFoundError(
                f"Meta file not found: {self._meta_path}. "
                f"Expected: services/artifacts/shanghai_model_v1.json"
            )

        with open(self._meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        # meta esperado
        freq_min = int(meta.get("freq_min", 15))
        lookback = int(meta.get("lookback", 20))
        offsets = meta.get("offsets", [2, 4, 6])

        if not isinstance(offsets, list) or not all(isinstance(x, (int, float)) for x in offsets):
            raise ValueError(f"Invalid 'offsets' in meta: {offsets}")

        offsets_int = [int(x) for x in offsets]

        GlucoseForecastService._config = ForecastConfig(
            freq_min=freq_min,
            lookback=lookback,
            offsets=offsets_int,
            target=str(meta.get("target", "glucose")),
            units=str(meta.get("units", "mg/dL")),
        )
        return GlucoseForecastService._config

    def _load_bundle(self) -> Tuple[tf.keras.Model, Any, ForecastConfig]:
        cfg = self._load_config()

        if GlucoseForecastService._model is None:
            if not self._model_path.exists():
                raise FileNotFoundError(
                    f"Model file not found: {self._model_path}. "
                    f"Expected: services/artifacts/shanghai_lstm_v1.keras"
                )
            GlucoseForecastService._model = tf.keras.models.load_model(str(self._model_path))

        if GlucoseForecastService._scaler is None:
            if not self._scaler_path.exists():
                raise FileNotFoundError(
                    f"Scaler file not found: {self._scaler_path}. "
                    f"Expected: services/artifacts/shanghai_scaler_v1.joblib"
                )
            GlucoseForecastService._scaler = joblib.load(str(self._scaler_path))

        return GlucoseForecastService._model, GlucoseForecastService._scaler, cfg

    def _prepare_input(self, ctx_values_mg_dl: List[float], lookback: int, scaler: Any) -> np.ndarray:
        """
        Replica o preprocessing do notebook:
          - pega CTX valores crus (mg/dL)
          - reshape (-1,1)
          - scaler.transform
          - reshape (1, CTX, 1)
        """
        if len(ctx_values_mg_dl) != lookback:
            raise ValueError(f"Expected lookback={lookback} values, got {len(ctx_values_mg_dl)}")

        x = np.array(ctx_values_mg_dl, dtype=np.float32).reshape(-1, 1)  # (CTX, 1)
        x_scaled = scaler.transform(x).astype(np.float32)                # (CTX, 1)
        return x_scaled.reshape(1, lookback, 1)                          # (1, CTX, 1)

    @staticmethod
    def _normalize_model_output(y_pred: Any, expected_len: int) -> np.ndarray:
        """
        Aceita outputs comuns:
          - (1, K)
          - (K,)
          - (1, K, 1)
          - etc.
        """
        arr = np.array(y_pred)
        arr = arr.reshape(-1)
        if arr.shape[0] != expected_len:
            raise ValueError(f"Model output size {arr.shape[0]} != expected {expected_len}")
        return arr.astype(np.float32)

    def forecast_from_anchor(self, anchor_time: datetime, ctx_values_mg_dl: List[float]) -> ForecastOutput:
        """
        anchor_time: timestamp do último ponto real usado como referência (t0)
        ctx_values_mg_dl: lista de tamanho LOOKBACK (ex.: 20), em mg/dL

        Retorna: previsões em mg/dL nos offsets definidos em meta.json (ex.: +30/+60/+90).
        """
        model, scaler, cfg = self._load_bundle()

        x = self._prepare_input(ctx_values_mg_dl, cfg.lookback, scaler)
        y_pred = model.predict(x, verbose=0)

        y = self._normalize_model_output(y_pred, expected_len=len(cfg.offsets))

        predicted: List[ForecastPoint] = []
        for off, val in zip(cfg.offsets, y.tolist()):
            ahead_min = cfg.freq_min * int(off)
            ts = anchor_time + timedelta(minutes=ahead_min)
            predicted.append(ForecastPoint(timestamp=ts, value_mg_dl=float(val), ahead_min=ahead_min))

        return ForecastOutput(anchor_time=anchor_time, config=cfg, predicted=predicted)

    def get_config(self) -> ForecastConfig:
        _, _, cfg = self._load_bundle()
        return cfg

    def healthcheck(self) -> Dict[str, Any]:
        model, scaler, cfg = self._load_bundle()
        return {
            "ok": True,
            "artifacts_dir": str(self._artifacts_dir),
            "model_loaded": model is not None,
            "scaler_loaded": scaler is not None,
            "freq_min": cfg.freq_min,
            "lookback": cfg.lookback,
            "offsets": cfg.offsets,
        }
