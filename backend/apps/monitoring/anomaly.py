"""Rule-based anomaly detection stub; replace with ML model later."""

from statistics import mean, stdev


class AnomalyDetector:
    def detect(self, values: list[float], threshold: float = 2.0) -> bool:
        if len(values) < 5:
            return False
        avg = mean(values)
        try:
            sd = stdev(values)
        except Exception:
            return False
        if sd == 0:
            return False
        z = abs((values[-1] - avg) / sd)
        return z > threshold
