import os
import httpx
from typing import Any, Dict
from datetime import datetime
from services.diabetic_service import DiabeticService
from services.nutrition_service import NutritionService
from services.judge_service import JudgeService
from services.plan_json_service import PlanJsonService
from services.causal_service import CausalService
from services.glucose_forecast_service import GlucoseForecastService


class GatewayService:
    def __init__(self):
        self._diabetic_url = os.getenv("DIABETIC_SERVICE_URL")
        self._nutrition_url = os.getenv("NUTRITION_SERVICE_URL")
        self._judge_url = os.getenv("JUDGE_SERVICE_URL")
        self._causal_url = os.getenv("CAUSAL_SERVICE_URL")
        self._diabetic_local = DiabeticService()
        self._nutrition_local = NutritionService()
        self._judge_local = JudgeService()
        self._plan_json_local = PlanJsonService()
        self._causal_local = CausalService()
        self._glucose_forecast_local = GlucoseForecastService()

    def _post(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    
    def glucose_forecast(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        payload esperado:
          - anchor_time: str ISO (ex.: "2024-01-10T12:00:00")
          - ctx_values_mg_dl: List[float] tamanho LOOKBACK
          - glucose_readings: List[{timestamp, value_mg_dl}] -> para métricas/alertas
        """
        anchor_time_iso = payload.get("anchor_time")
        ctx_values = payload.get("ctx_values_mg_dl", [])
        glucose_readings = payload.get("glucose_readings", [])

        if not anchor_time_iso:
            raise ValueError("payload.anchor_time is required (ISO string)")
        if not isinstance(ctx_values, list) or len(ctx_values) == 0:
            raise ValueError("payload.ctx_values_mg_dl is required (non-empty list)")

        try:
            anchor_dt = datetime.fromisoformat(anchor_time_iso.replace("Z", "+00:00"))
        except Exception as e:
            raise ValueError(f"Invalid anchor_time ISO: {anchor_time_iso}") from e

        fc = self._glucose_forecast_local.forecast_from_anchor(anchor_dt, ctx_values)

        predicted_points = [
            {
                "timestamp": p.timestamp.isoformat(),
                "value_mg_dl": float(p.value_mg_dl),
                "ahead_min": int(p.ahead_min),
                "type": "predicted",
            }
            for p in fc.predicted
        ]

        diabetic = self.diabetic_analyze({"glucose_readings": glucose_readings})

        return {
            "forecast": {
                "freq_min": fc.config.freq_min,
                "lookback": fc.config.lookback,
                "offsets": fc.config.offsets,
                "anchor_time": anchor_dt.isoformat(),
                "predicted_points": predicted_points,
            },
            "diabetic_analysis": diabetic,
        }

    def diabetic_analyze(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self._diabetic_url:
            try:
                return self._post(f"{self._diabetic_url}/diabetic/analyze", payload)
            except Exception:
                pass
        return self._diabetic_local.analyze(payload.get("glucose_readings", []))

    def nutrition_analyze(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self._nutrition_url:
            try:
                return self._post(f"{self._nutrition_url}/nutrition/analyze", payload)
            except Exception:
                pass
        return self._nutrition_local.analyze(payload)

    def judge_consolidate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self._judge_url:
            try:
                return self._post(f"{self._judge_url}/judge/consolidate", payload)
            except Exception:
                pass
        return self._judge_local.consolidate(payload)

    def causal_analyze(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self._causal_url:
            try:
                return self._post(f"{self._causal_url}/causal/analyze", payload)
            except Exception:
                pass
        return self._causal_local.analyze(payload)

    def generate_plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        diabetic = self.diabetic_analyze(payload)
        causal = self.causal_analyze(payload)
        nutrition = self.nutrition_analyze(payload)
        judge_payload = {
            "nutrition_plan": nutrition.get("nutrition_plan", ""),
            "diabetic_analysis": {"metrics": diabetic.get("metrics"), "alerts": diabetic.get("alerts"), "causal": causal},
            "restrictions": payload.get("restrictions", []),
            "goals": payload.get("goals", []),
            "inventory": payload.get("inventory", []),
        }
        judge = self.judge_consolidate(judge_payload)
        final_plan_text = judge.get("final_plan", "")
        
        # Format plan as JSON
        plan_json = self._plan_json_local.format(final_plan_text, diabetic)
        
        # Ensure plan_json is never empty
        if not plan_json or len(plan_json) == 0:
            # Last resort fallback
            from services.plan_json_service import PlanJsonService
            fallback_service = PlanJsonService()
            plan_json = fallback_service._create_fallback_structure(final_plan_text, diabetic)

        return {
            "diabetic_analysis": diabetic,
            "causal_analysis": causal,
            "nutrition": nutrition,
            "judge": judge,
            "final_plan": final_plan_text,
            "plan_json": plan_json,
        }

