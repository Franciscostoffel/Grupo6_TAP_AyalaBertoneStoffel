"""Errores que puede dar el análisis.

El servicio los lanza con "raise" y la ruta de la API los convierte en una
respuesta HTTP con el código correspondiente (503, 422 o 404).
"""


class DataNotReadyError(Exception):
    """Todavía no hay datos en la base (se están descargando). -> HTTP 503"""


class InvalidRiskError(Exception):
    """El riesgo no es "bajo", "moderado" ni "alto". -> HTTP 422"""


class NoOptionsError(Exception):
    """Ningún producto es compatible con el riesgo elegido. -> HTTP 404"""


class EmailAlreadyRegisteredError(Exception):
    """El email ya tiene una cuenta. -> HTTP 409"""


class InvalidCredentialsError(Exception):
    """El email o la contraseña no son correctos. -> HTTP 401"""
