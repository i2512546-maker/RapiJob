import os
import uuid

os.environ["DATABASE_URL"] = "sqlite:///./test_rapijob.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-rapijob"

from fastapi.testclient import TestClient
from main import app


def register(client, role):
    email = f"{role}-{uuid.uuid4().hex[:8]}@example.com"
    response = client.post("/api/auth/registro", json={
        "nombre": "Usuario",
        "apellido": "Prueba",
        "email": email,
        "telefono": "999999999",
        "tipo_usuario": role,
        "contraseña": "ClaveSegura123",
    })
    assert response.status_code == 201, response.text
    login = client.post("/api/auth/login", json={
        "email": email,
        "contraseña": "ClaveSegura123",
    })
    assert login.status_code == 200, login.text
    return email, login.json()["access_token"]


def test_registration_catalog_and_booking_flow():
    with TestClient(app) as client:
        _, client_token = register(client, "cliente")
        _, technician_token = register(client, "tecnico")

        services = client.get("/api/servicios/")
        assert services.status_code == 200
        assert services.json()
        service = services.json()[0]

        slots = client.get("/api/admin/slots-citas/")
        assert slots.status_code == 200
        assert slots.json()
        slot = slots.json()[0]

        created = client.post(
            "/api/ordenes/",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "id_servicio": service["id_servicio"],
                "id_slot_cita": slot["id_slot"],
                "ubicacion_servicio": "Huancayo, Junín",
                "descripcion_problema": "Mi computadora se reinicia y necesito un diagnóstico.",
                "notas_adicionales": "Llamar antes de llegar.",
            },
        )
        assert created.status_code == 201, created.text
        order_id = created.json()["id_orden"]
        assert created.json()["precio_final"] is not None

        client_orders = client.get(
            "/api/ordenes/",
            headers={"Authorization": f"Bearer {client_token}"},
        )
        assert client_orders.status_code == 200
        assert any(order["id_orden"] == order_id for order in client_orders.json())

        accepted = client.patch(
            f"/api/ordenes/{order_id}/aceptar",
            headers={"Authorization": f"Bearer {technician_token}"},
        )
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()["estado_orden"] == "aceptada"
