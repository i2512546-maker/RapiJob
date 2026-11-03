from fastapi import APIRouter

# RapiJob muestra precios referenciales y registra solicitudes.
# No cobra ni solicita datos bancarios en esta versión.
router = APIRouter(prefix="/api/admin/metodos-pago", tags=["pagos-desactivados"])


@router.get("/")
def pagos_no_disponibles():
    return []
