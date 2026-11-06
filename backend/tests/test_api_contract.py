import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import (  # noqa: E402
    ClienteIn,
    CreditoIn,
    PagoIn,
    app,
)


class ApiContractTests(unittest.TestCase):
    def test_required_routes_are_registered(self):
        paths = {route.path for route in app.routes}
        for path in (
            "/api/health",
            "/api/dashboard",
            "/api/clientes",
            "/api/creditos",
            "/api/pagos",
            "/api/predicciones",
            "/api/cobranzas",
            "/api/alertas",
            "/api/reportes/cartera",
            "/api/asistente",
        ):
            with self.subTest(path=path):
                self.assertIn(path, paths)

    def test_invalid_financial_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            PagoIn(cuota_id="00000000-0000-0000-0000-000000000001", monto=0)
        with self.assertRaises(ValueError):
            ClienteIn(
                codigo="CLI-1",
                tipo_documento="DNI",
                numero_documento="12345678",
                nombres="Ana",
                apellidos="Pérez",
                correo="correo-invalido",
            )
        with self.assertRaises(ValueError):
            CreditoIn(
                codigo="CR-1",
                cliente_id="00000000-0000-0000-0000-000000000001",
                monto=100,
                tasa_interes=10,
                plazo_meses=12,
                frecuencia_pago="anual",
                fecha_desembolso="2026-01-01",
                fecha_vencimiento="2027-01-01",
            )


if __name__ == "__main__":
    unittest.main()
