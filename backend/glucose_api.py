from __future__ import annotations

import io
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from .storage import (
    create_glucose_session,
    list_glucose_sessions,
    get_glucose_session,
)
from services.gateway_service import GatewayService
from services.glucose_forecast_service import GlucoseForecastService


router = APIRouter(prefix="/glucose-sessions", tags=["glucose"])
gateway_service = GatewayService()
forecast_service = GlucoseForecastService()


REQUIRED_COLS = {"timestamp", "glucose", "patient_id", "session_id"}


def _parse_csv_upload(file: UploadFile) -> pd.DataFrame:
    raw = file.file.read()
    try:
        text = raw.decode("utf-8")
    except Exception:
        # fallback comum em CSVs brasileiros
        text = raw.decode("latin-1")

    df = pd.read_csv(io.StringIO(text))

    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV inválido. Faltando colunas obrigatórias: {sorted(list(missing))}",
        )

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["glucose"] = pd.to_numeric(df["glucose"], errors="coerce")
    df = df.dropna(subset=["timestamp", "glucose"]).copy()

    # regra da sprint: 1 paciente por upload
    patient_ids = df["patient_id"].dropna().unique().tolist()
    if len(patient_ids) != 1:
        raise HTTPException(
            status_code=400,
            detail=f"Regra da sprint: CSV deve conter 1 único patient_id. Encontrados: {patient_ids}",
        )

    # por simplicidade nesta sprint: 1 session_id por upload também
    session_ids = df["session_id"].dropna().unique().tolist()
    if len(session_ids) != 1:
        raise HTTPException(
            status_code=400,
            detail=f"Nesta sprint, aceite apenas 1 session_id por upload. Encontrados: {session_ids}",
        )

    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last").reset_index(drop=True)
    lookback = forecast_service.get_config().lookback
    if len(df) < lookback:
        raise HTTPException(
            status_code=400,
            detail=f"Poucos pontos para inferência. Precisa >= {lookback}, veio {len(df)}.",
        )

    return df


def _compute_trend(values: List[float]) -> str:
    # regra simples para sprint: delta no período de 60min
    if len(values) < 2:
        return "stable"
    delta = float(values[-1] - values[0])
    if abs(delta) < 5.0:
        return "stable"
    return "rising" if delta > 0 else "falling"


def _build_dashboard_payload(df: pd.DataFrame) -> Dict[str, Any]:
    patient_id = str(df["patient_id"].iloc[0])
    session_id = str(df["session_id"].iloc[0])

    cfg = forecast_service.get_config()
    max_off = max(cfg.offsets)

    # 1. Definir Âncora
    anchor_idx = len(df) - 1 - max_off
    if anchor_idx < (cfg.lookback - 1):
        anchor_idx = len(df) - 1 
        if anchor_idx < cfg.lookback:
             raise HTTPException(
                status_code=400,
                detail=f"CSV muito curto. Precisa de pelo menos {cfg.lookback} pontos."
            )

    anchor_time = df["timestamp"].iloc[anchor_idx].to_pydatetime()
    current_value = float(df["glucose"].iloc[anchor_idx]) # Valor exato no momento zero

    # 2. Contexto
    ctx_df = df.iloc[anchor_idx - cfg.lookback + 1 : anchor_idx + 1]
    ctx_values = ctx_df["glucose"].astype(float).tolist()

    # 3. Janela do Gráfico
    chart_start = anchor_time - timedelta(minutes=60)
    chart_end = anchor_time + timedelta(minutes=cfg.freq_min * max_off)

    chart_df = df[(df["timestamp"] >= chart_start) & (df["timestamp"] <= chart_end)].copy()

    # 4. Observado (Azul)
    observed_points = [
        {
            "timestamp": t.isoformat(),
            "value_mg_dl": float(v),
            "type": "observed",
        }
        for t, v in zip(
            chart_df["timestamp"].dt.to_pydatetime().tolist(),
            chart_df["glucose"].astype(float).tolist()
        )
    ]

    # 5. Previsão (Vermelho)
    fc = forecast_service.forecast_from_anchor(anchor_time=anchor_time, ctx_values_mg_dl=ctx_values)
    
    predicted_points = []
    
    # --- CORREÇÃO FUNDAMENTAL: Inserir o Ponto de Conexão ---
    # Adicionamos o valor atual como o primeiro ponto da previsão (T=0)
    # Isso faz a linha vermelha "nascer" da linha azul visualmente
    predicted_points.append({
        "timestamp": anchor_time.isoformat(),
        "value_mg_dl": current_value,
        "type": "predicted"
    })

    # Adiciona os pontos futuros do modelo (+30, +60, +90)
    for p in fc.predicted:
        predicted_points.append({
            "timestamp": p.timestamp.isoformat(),
            "value_mg_dl": float(p.value_mg_dl),
            "type": "predicted",
        })

    # 6. Estatísticas
    diabetic_payload = {
        "glucose_readings": [{"value_mg_dl": p["value_mg_dl"]} for p in observed_points]
    }
    diabetic_analysis = gateway_service.diabetic_analyze(diabetic_payload)
    metrics_raw = diabetic_analysis.get("metrics", {})

    glucose_stats = {
        "tir": metrics_raw.get("tir_pct", 0),
        "tar": metrics_raw.get("tar_pct", 0),
        "tbr": metrics_raw.get("tbr_pct", 0),
        "average": metrics_raw.get("avg_mg_dl", 0),
        "count": metrics_raw.get("count", 0)
    }

    # 7. Cards e Alertas
    current = current_value
    avg_recent = glucose_stats["average"]
    hba1c = float((avg_recent + 46.7) / 28.7) if avg_recent > 0 else 0.0
    trend = _compute_trend(ctx_values[-5:]) 

    alerts: List[str] = []
    pred_values = [float(p["value_mg_dl"]) for p in predicted_points]

    if any(v < 70 for v in pred_values):
        alerts.append("Previsão indica risco de hipoglicemia (<70 mg/dL).")
    if any(v > 250 for v in pred_values):
        alerts.append("Previsão indica possível pico glicêmico (>250 mg/dL).")
    
    alerts.extend(diabetic_analysis.get("alerts", []) or [])

    return {
        "meta": {
            "patient_id": patient_id,
            "session_id": session_id,
            "anchor_time": anchor_time.isoformat(),
        },
        "points": observed_points + predicted_points,
        "glucoseStats": glucose_stats,
        "cards": {
            "current_mg_dl": round(current, 2),
            "average_mg_dl": round(avg_recent, 2),
            "estimated_hba1c_pct": round(hba1c, 2),
            "trend": trend,
        },
        "alerts": alerts,
    }


@router.post("/upload")
async def upload_glucose_session(
    file: UploadFile = File(...),
    user_id: int = Form(1),  # sprint: default 1 se front ainda não passa auth
) -> Dict[str, Any]:
    df = _parse_csv_upload(file)
    dashboard = _build_dashboard_payload(df)

    patient_id = dashboard["meta"]["patient_id"]
    source_session_id = dashboard["meta"]["session_id"]
    anchor_time = dashboard["meta"]["anchor_time"]

    db_id = create_glucose_session(
        user_id=user_id,
        patient_id=patient_id,
        source_session_id=source_session_id,
        anchor_time_iso=anchor_time,
        dashboard_payload=dashboard,
    )

    dashboard["db_session_id"] = db_id
    return dashboard


@router.get("")
def list_sessions(user_id: int = 1, limit: int = 50) -> Dict[str, Any]:
    items = list_glucose_sessions(user_id=user_id, limit=limit)
    return {"success": True, "items": items}


@router.get("/{db_session_id}")
def get_session(db_session_id: int, user_id: int = 1) -> Dict[str, Any]:
    row = get_glucose_session(db_session_id=db_session_id, user_id=user_id)
    if not row:
        raise HTTPException(status_code=404, detail="Glucose session not found")
    return {"success": True, "item": row}
