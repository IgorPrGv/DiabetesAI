import pandas as pd
from typing import Any, Dict, List
from sklearn.linear_model import LinearRegression
from dowhy import CausalModel


class CausalService:
    def analyze(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        meal_history = payload.get("meal_history", [])
        glucose_readings = payload.get("glucose_readings", [])

        if len(glucose_readings) < 3:
            return {
                "status": "insufficient_data",
                "message": "Need at least 3 glucose readings for causal analysis.",
            }

        meal_scores = self._meal_carbs_proxy(meal_history)
        if not meal_scores:
            meal_scores = [1.0]

        rows = []
        for i, reading in enumerate(glucose_readings):
            value = reading.get("value_mg_dl")
            ts = reading.get("timestamp")
            if value is None:
                continue
            carbs_proxy = meal_scores[i % len(meal_scores)]
            hour = self._hour_from_timestamp(ts)
            rows.append(
                {
                    "carbs_proxy": carbs_proxy,
                    "hour": hour,
                    "glucose": value,
                }
            )

        if len(rows) < 3:
            return {
                "status": "insufficient_data",
                "message": "Not enough valid glucose readings for causal analysis.",
            }

        df = pd.DataFrame(rows)

        regression = LinearRegression()
        regression.fit(df[["carbs_proxy", "hour"]], df["glucose"])
        coef_carbs = float(regression.coef_[0])
        coef_hour = float(regression.coef_[1])

        causal_result = {
            "status": "ok",
            "model": "backdoor.linear_regression",
            "treatment": "carbs_proxy",
            "outcome": "glucose",
            "effect": None,
            "regression": {"coef_carbs": coef_carbs, "coef_hour": coef_hour},
        }

        try:
            model = CausalModel(
                data=df,
                treatment="carbs_proxy",
                outcome="glucose",
                common_causes=["hour"],
            )
            estimand = model.identify_effect()
            estimate = model.estimate_effect(estimand, method_name="backdoor.linear_regression")
            causal_result["effect"] = float(estimate.value)
        except Exception as exc:
            causal_result["status"] = "fallback"
            causal_result["message"] = f"DoWhy failed, using regression only: {exc}"

        causal_result["insights"] = self._build_insights(causal_result)
        return causal_result

    def _meal_carbs_proxy(self, meals: List[str]) -> List[float]:
        keywords = {
            "arroz": 2.0,
            "pão": 2.0,
            "massa": 2.0,
            "macarr": 2.0,
            "batata": 1.5,
            "feijão": 1.0,
            "fruta": 0.8,
            "salada": 0.5,
            "legume": 0.5,
            "doce": 2.5,
            "açúcar": 2.5,
        }

        scores = []
        for meal in meals:
            text = (meal or "").lower()
            score = 0.5
            for key, weight in keywords.items():
                if key in text:
                    score += weight
            scores.append(round(score, 2))
        return scores

    def _hour_from_timestamp(self, ts: str) -> int:
        try:
            dt = pd.to_datetime(ts, errors="coerce")
            if pd.isna(dt):
                return 0
            return int(dt.hour)
        except Exception:
            return 0

    def _build_insights(self, result: Dict[str, Any]) -> List[str]:
        insights = []
        coef = result.get("regression", {}).get("coef_carbs")
        effect = result.get("effect")
        if coef is not None:
            if coef > 0:
                insights.append("Maior carga de carboidratos tende a elevar glicemia.")
            elif coef < 0:
                insights.append("Maior carga de carboidratos tende a reduzir glicemia (verifique dados).")
            else:
                insights.append("Sem relação clara entre carboidratos e glicemia nesta amostra.")
        if effect is not None:
            insights.append(f"Efeito causal estimado: {effect:.2f} mg/dL por unidade de carboidrato proxy.")
        return insights

