# Arquitectura Profesional de Citas y Órdenes - RapiJob

## Flujo de Creación de Orden

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENTE SOLICITA SERVICIO                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                ┌──────────▼──────────┐
                │ 1. Ver slots        │
                │    disponibles      │
                │ GET /slots-citas    │
                └──────────┬──────────┘
                           │
                ┌──────────▼────────────────┐
                │ 2. Seleccionar:           │
                │   - Fecha/Hora (slot)    │
                │   - Servicio              │
                │   - Método pago           │
                │   - Descripción (≤1000)   │
                │   - Notas (≤500)          │
                │   - Precio negociado (opt)│
                └──────────┬────────────────┘
                           │
                ┌──────────▼──────────────────────────┐
                │ 3. Crear orden                       │
                │ POST /api/ordenes/                  │
                │                                     │
                │ ✓ Valida slot disponible           │
                │ ✓ Valida método pago activo        │
                │ ✓ Valida precio (min 50% base)     │
                │ ✓ Reserva slot (+1 contador)       │
                │ ✓ Estado: PENDIENTE                │
                │ ✓ Estado Pago: PENDIENTE           │
                └──────────┬──────────────────────────┘
                           │
         ┌─────────────────┴────────────────────┐
         │                                      │
    ┌────▼──────────┐            ┌────────────▼─────┐
    │ CLIENTE:      │            │ TÉCNICOS ven:    │
    │ Ver orden     │            │ Órdenes         │
    │ Negociar      │            │ disponibles      │
    │ precio        │            │ PENDIENTE        │
    │ Cancelar      │            │                  │
    └───────────────┘            └─────────┬────────┘
                                           │
                            ┌──────────────▼──────────────┐
                            │ 4. Técnico acepta orden    │
                            │ PATCH /ordenes/{id}/aceptar│
                            │                            │
                            │ ✓ Asigna técnico           │
                            │ ✓ Estado: ACEPTADA         │
                            └────────────────────────────┘
```

## Tabla: MetodoPago (Administrador)

```
┌──────────────────────────────────────────────────────┐
│                  METODOS_PAGO                        │
├──────────────────────────────────────────────────────┤
│ id_metodo (PK)         │ INTEGER                     │
│ nombre_metodo (UNIQUE) │ VARCHAR(50)                 │
│                        │ ej: "Tarjeta Crédito"      │
│ descripcion            │ VARCHAR(255)                │
│ estado                 │ ENUM('activo', 'inactivo')  │
│ require_verificacion   │ BOOLEAN                     │
│ comision_porcentaje    │ DECIMAL(5,2)                │
│ fecha_creacion         │ DATETIME                    │
└──────────────────────────────────────────────────────┘

OPERACIONES:
- Admin crea métodos (POST /api/admin/metodos-pago/)
- Admin desactiva/activa (PATCH /api/admin/metodos-pago/{id})
- Clientes ven métodos activos (GET /api/admin/metodos-pago/)
```

## Tabla: SlotCita (Administrador)

```
┌────────────────────────────────────────────────────────┐
│                   SLOTS_CITAS                          │
├────────────────────────────────────────────────────────┤
│ id_slot (PK)          │ INTEGER                        │
│ fecha                 │ DATETIME                       │
│ hora_inicio           │ DATETIME                       │
│ hora_fin              │ DATETIME                       │
│ capacidad_maxima      │ INTEGER (default: 1)          │
│ reservas_actuales     │ INTEGER                        │
│ estado                │ ENUM('disponible',             │
│                       │       'lleno',                │
│                       │       'bloqueado')            │
│ fecha_creacion        │ DATETIME                       │
└────────────────────────────────────────────────────────┘

LÓGICA:
- Admin crea slots administrativos
- Si reservas_actuales >= capacidad_maxima → LLENO
- Clientes reservan slot al crear orden
- Admin puede bloquear/desbloquear
- Admin puede liberar reservas manualmente

VALIDACIONES:
✓ No se permiten solapamientos de horarios
✓ hora_inicio < hora_fin
✓ Incremento automático de reservas
```

## Tabla: OrdenTrabajo (Refactorizada)

```
┌─────────────────────────────────────────────────────────┐
│                  ORDENES_TRABAJO                        │
├─────────────────────────────────────────────────────────┤
│ REFERENCIA Y RELACIONES:                               │
│ id_cliente            │ FK → usuarios                   │
│ id_tecnico            │ FK → perfiles_tecnicos (NULL)   │
│ id_servicio           │ FK → servicios                  │
│ id_slot_cita (NEW)    │ FK → slots_citas               │
│ id_metodo_pago (NEW)  │ FK → metodos_pago              │
│                                                         │
│ DESCRIPCIÓN:                                            │
│ descripcion_problema  │ VARCHAR(1000) ← LÍMITE FIJO   │
│ notas_adicionales     │ VARCHAR(500) ← LÍMITE FIJO    │
│                                                         │
│ PRECIO (Profesional):                                   │
│ precio_base           │ DECIMAL (del servicio)         │
│ precio_negociado      │ DECIMAL (NULL o valor)         │
│                       │ min = 50% precio_base         │
│ precio_final          │ DECIMAL (auto calculado)       │
│                                                         │
│ ESTADOS SEPARADOS:                                      │
│ estado_orden          │ ENUM('pendiente',               │
│                       │       'aceptada',               │
│                       │       'en_progreso',            │
│                       │       'completada',             │
│                       │       'cancelada')              │
│                                                         │
│ estado_pago           │ ENUM('pendiente',               │
│                       │       'procesando',             │
│                       │       'completado',             │
│                       │       'rechazado')              │
│                                                         │
│ razon_cancelacion     │ VARCHAR(255)                    │
│ referencia_transaccion│ VARCHAR(100)                    │
│ fecha_solicitud       │ DATETIME                        │
│ fecha_completada      │ DATETIME                        │
│ fecha_pago            │ DATETIME                        │
└─────────────────────────────────────────────────────────┘
```

## Endpoints Profesionales

### CLIENTE - Crear Orden

```bash
POST /api/ordenes/

{
  "id_servicio": 1,
  "id_slot_cita": 5,              ← Reservar slot disponible
  "id_metodo_pago": 2,             ← Seleccionar método
  "ubicacion_servicio": "Calle 123, Apt 4B",
  "descripcion_problema": "La computadora no inicia, hace ruido extraño...",  ← Max 1000
  "notas_adicionales": "Mejor antes de las 10am",  ← Max 500
  "precio_negociado": 150.00      ← Opcional (min 50% base)
}

RESPUESTA:
{
  "id_orden": 1,
  "estado_orden": "pendiente",
  "estado_pago": "pendiente",
  "precio_base": 300.00,
  "precio_negociado": 150.00,
  "precio_final": 150.00,
  "id_slot_cita": 5,
  "id_metodo_pago": 2
}
```

### CLIENTE - Negociar Precio

```bash
PATCH /api/ordenes/1/negociar-precio

{
  "precio_negociado": 200.00
}

VALIDACIÓN:
✓ Orden debe estar en estado PENDIENTE
✓ Precio >= 50% del precio_base
✗ No se puede negociar después de aceptada
```

### CLIENTE - Cancelar Orden

```bash
PATCH /api/ordenes/1/cancelar?razon=Cambié+de+idea

LÓGICA:
✓ Libera el slot (reservas_actuales -= 1)
✓ Si slot estaba LLENO → pasa a DISPONIBLE
✓ Registra razón de cancelación
✓ Solo en estados: PENDIENTE, ACEPTADA
```

### ADMIN - Crear Método de Pago

```bash
POST /api/admin/metodos-pago/

{
  "nombre_metodo": "Tarjeta Crédito",
  "descripcion": "Visa, Mastercard, Amex",
  "comision_porcentaje": 2.5,
  "require_verificacion": true
}
```

### ADMIN - Crear Slots de Citas

```bash
POST /api/admin/slots-citas/

{
  "fecha": "2026-09-20",
  "hora_inicio": "2026-09-20T09:00:00",
  "hora_fin": "2026-09-20T10:00:00",
  "capacidad_maxima": 2
}

VALIDACIONES:
✓ hora_inicio < hora_fin
✓ No solapamientos con otros slots
✓ Validación de conflictos horarios
```

### ADMIN - Gestión de Slots

```bash
# Ver disponibles
GET /api/admin/slots-citas/?fecha_desde=...&fecha_hasta=...

# Bloquear (mantenimiento)
PATCH /api/admin/slots-citas/5/bloquear

# Liberar manualmente
PATCH /api/admin/slots-citas/5/liberar
```

## Flujo de Estados

```
ORDEN:
pendiente → aceptada → en_progreso → completada
    ↓
  cancelada (en cualquier momento)

PAGO:
pendiente → procesando → completado
    ↓
  rechazado (cualquier momento)
    ↓
  reembolsado (si fue completado antes)
```

## Validaciones Profesionales

```
✓ Descripción: 10-1000 caracteres
✓ Notas: 0-500 caracteres
✓ Precio negociado: >= 50% del base, <= 200% del base
✓ Slot debe estar DISPONIBLE
✓ Método pago debe estar ACTIVO
✓ No permitir cancelación después de COMPLETADA
✓ No permitir negociar después de ACEPTADA
✓ Slot se reserva automáticamente al crear orden
✓ Slot se libera automáticamente al cancelar orden
✓ Validación de solapamientos de horarios en slots
```

## Diferencias Clave (Antes vs Ahora)

```
ANTES (Simple):
├─ Fecha como columna simple
├─ Método pago como ENUM fijo
├─ Descripción sin límites
├─ Precio fijo, sin negociación
└─ Sin gestión de slots

AHORA (Profesional):
├─ Slots administrativos (tabla separada)
├─ Métodos pago configurables por admin
├─ Descripción/notas con límites claros
├─ Precio base + negociable
├─ Validación de capacidad y disponibilidad
├─ Separación clara: estado_orden vs estado_pago
├─ Trazabilidad de transacciones
└─ Gestión administrativa robusta
```
