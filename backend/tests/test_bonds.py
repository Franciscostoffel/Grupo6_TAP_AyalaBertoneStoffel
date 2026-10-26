"""Pruebas del apartado de bonos sin tocar la base de datos ni la red."""

import unittest
from datetime import date, datetime, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes import bonds
from backend.domain.bonds import normalize_cer_bond, normalize_fixed_rate_bill
from backend.domain.returns import effective_period_return_pct
from backend.services import auth_service, bond_service
from backend.services.exceptions import DataNotReadyError

LETRA = {"ticker": "T15E7", "precioArs": 152.74, "tnaPorcentaje": 24.68,
         "teaPorcentaje": 27.15, "fechaVencimiento": "2027-01-15"}
BONO_CER = {"ticker": "TZXD7", "precioArs": 291.55, "tirPorcentaje": -1.2,
            "fechaVencimiento": "2027-12-15"}


class BondDomainTests(unittest.TestCase):
    def test_fixed_rate_bill_is_normalized(self):
        bono = normalize_fixed_rate_bill(LETRA)
        self.assertEqual((bono["tna"], bono["tea"], bono["tir"]), (24.68, 27.15, None))

    def test_unreliable_bills_are_discarded(self):
        # Dual con tasas negativas y bono sin precio.
        self.assertIsNone(normalize_fixed_rate_bill({**LETRA, "tnaPorcentaje": -58.18, "teaPorcentaje": -45.47}))
        self.assertIsNone(normalize_fixed_rate_bill({**LETRA, "precioArs": 0}))

    def test_cer_bond_keeps_negative_real_rate(self):
        self.assertEqual(normalize_cer_bond(BONO_CER)["tir"], -1.2)
        self.assertIsNone(normalize_cer_bond({**BONO_CER, "tirPorcentaje": None}))

    def test_effective_return(self):
        self.assertAlmostEqual(effective_period_return_pct(26, 365), 26)
        self.assertAlmostEqual(effective_period_return_pct(26, 90), 5.8641, places=3)


class BondServiceTests(unittest.TestCase):
    def guardado(self, bono, vencimiento):
        """Así devuelve el repositorio un bono: con la fecha como date."""
        return {**bono, "fecha_vencimiento": vencimiento}

    def test_splits_by_type_skips_expired_and_long_bonds_and_calculates_gain(self):
        letra = self.guardado(normalize_fixed_rate_bill(LETRA), date(2027, 1, 15))
        vencida = self.guardado(normalize_fixed_rate_bill({**LETRA, "ticker": "S30O6"}), date(2026, 10, 1))
        # Bono con cupones a más de un año (TY30P): no se muestra.
        lejana = self.guardado(normalize_fixed_rate_bill({**LETRA, "ticker": "TY30P"}), date(2030, 5, 30))
        cer = self.guardado(normalize_cer_bond(BONO_CER), date(2027, 12, 15))

        with patch.object(bond_service.bond_repository, "get_bonds", return_value=[vencida, letra, lejana, cer]), \
             patch.object(bond_service, "datetime") as reloj:
            reloj.now.return_value = datetime(2026, 10, 26)
            resultado = bond_service.list_bonds(capital=1_000_000)

        self.assertEqual([b.ticker for b in resultado.tasa_fija], ["T15E7"])
        self.assertEqual([b.ticker for b in resultado.cer], ["TZXD7"])
        letra_resultado = resultado.tasa_fija[0]
        esperado = 1_000_000 * effective_period_return_pct(27.15, 81) / 100
        self.assertEqual(letra_resultado.dias_al_vencimiento, 81)
        self.assertAlmostEqual(letra_resultado.ganancia, esperado, places=1)
        self.assertIsNone(resultado.cer[0].ganancia)

    def test_without_capital_there_is_no_gain(self):
        letra = self.guardado(normalize_fixed_rate_bill(LETRA), date(2027, 1, 15))
        with patch.object(bond_service.bond_repository, "get_bonds", return_value=[letra]), \
             patch.object(bond_service, "datetime") as reloj:
            reloj.now.return_value = datetime(2026, 10, 26)
            resultado = bond_service.list_bonds()
        self.assertIsNone(resultado.tasa_fija[0].ganancia)
        self.assertIsNotNone(resultado.tasa_fija[0].rendimiento_pct)

    def test_empty_table_means_data_not_ready(self):
        with patch.object(bond_service.bond_repository, "get_bonds", return_value=[]):
            with self.assertRaises(DataNotReadyError):
                bond_service.list_bonds()


class BondHttpTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(bonds.router)
        self.client = TestClient(app)
        self.user = {"id": uuid4(), "email": "person@example.com", "created_at": datetime.now(timezone.utc)}
        self.respuesta = {"capital": None, "tasa_fija": [], "cer": []}

    def test_requires_session(self):
        with patch.object(auth_service, "get_current_user", return_value=None):
            self.assertEqual(self.client.get("/api/bonds").status_code, 401)

    def test_passes_capital_and_validates_it(self):
        with patch.object(auth_service, "get_current_user", return_value=self.user), \
             patch.object(bonds.bond_service, "list_bonds", return_value=self.respuesta) as listar:
            self.assertEqual(self.client.get("/api/bonds?capital=5000").status_code, 200)
            listar.assert_called_once_with(5000)
            self.assertEqual(self.client.get("/api/bonds?capital=-1").status_code, 422)

    def test_data_not_ready_is_503(self):
        with patch.object(auth_service, "get_current_user", return_value=self.user), \
             patch.object(bonds.bond_service, "list_bonds", side_effect=DataNotReadyError("Sincronizando")):
            self.assertEqual(self.client.get("/api/bonds").status_code, 503)


if __name__ == "__main__":
    unittest.main()
