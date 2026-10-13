"""Errores de los servicios. La capa API los traduce a respuestas HTTP."""


class AnalysisError(Exception):
    """Error esperado del análisis; el mensaje se muestra al usuario."""


class DataNotReadyError(AnalysisError):
    """Todavía no hay datos sincronizados en la caché."""


class InvalidRiskError(AnalysisError):
    """El nivel de riesgo recibido no es bajo, moderado ni alto."""


class NoOptionsError(AnalysisError):
    """Ningún producto es compatible con el riesgo elegido."""
