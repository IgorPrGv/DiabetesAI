from typing import Any, Dict, List


class DiabeticService:
    def analyze(self, glucose_readings: List[Dict[str, Any]]) -> Dict[str, Any]:
        metrics = self._compute_glycemic_metrics(glucose_readings)
        alerts = self._generate_alerts(metrics)
        return {
            "metrics": metrics,
            "alerts": alerts,
        }

    def _compute_glycemic_metrics(self, glucose_readings: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not glucose_readings:
            return {
                "count": 0,
                "tir_pct": None,
                "tar_pct": None,
                "tbr_pct": None,
                "avg_mg_dl": None,
                "min_mg_dl": None,
                "max_mg_dl": None,
            }

        values = [reading.get("value_mg_dl") for reading in glucose_readings if reading.get("value_mg_dl") is not None]
        if not values:
            return {
                "count": 0,
                "tir_pct": None,
                "tar_pct": None,
                "tbr_pct": None,
                "avg_mg_dl": None,
                "min_mg_dl": None,
                "max_mg_dl": None,
            }

        total = len(values)
        tir = sum(1 for v in values if 70 <= v <= 180)
        tar = sum(1 for v in values if v > 180)
        tbr = sum(1 for v in values if v < 70)
        avg = sum(values) / total

        return {
            "count": total,
            "tir_pct": round((tir / total) * 100, 2),
            "tar_pct": round((tar / total) * 100, 2),
            "tbr_pct": round((tbr / total) * 100, 2),
            "avg_mg_dl": round(avg, 2),
            "min_mg_dl": min(values),
            "max_mg_dl": max(values),
        }

    def _generate_alerts(self, metrics: Dict[str, Any]) -> List[str]:
        alerts = []
        tbr = metrics.get("tbr_pct")
        tar = metrics.get("tar_pct")
        max_val = metrics.get("max_mg_dl")
        min_val = metrics.get("min_mg_dl")

        if tbr is not None and tbr > 5:
            alerts.append("Risco de hipoglicemia: tempo abaixo da faixa alvo elevado.")
        if tar is not None and tar > 25:
            alerts.append("Risco de hiperglicemia: tempo acima da faixa alvo elevado.")
        if max_val is not None and max_val > 250:
            alerts.append("Pico glicêmico alto identificado (>250 mg/dL).")
        if min_val is not None and min_val < 60:
            alerts.append("Leitura muito baixa identificada (<60 mg/dL).")

        return alerts


