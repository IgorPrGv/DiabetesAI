import os
import httpx
from typing import Any, Dict
from services.diabetic_service import DiabeticService
from services.nutrition_service import NutritionService
from services.judge_service import JudgeService
from services.plan_json_service import PlanJsonService
from services.causal_service import CausalService


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

    def _post(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

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

