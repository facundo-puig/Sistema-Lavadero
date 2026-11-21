# API de turnos

Contrato de los endpoints del bloque de turnos. Define qué envía y qué devuelve cada endpoint, para que el backend y el frontend se trabajen en paralelo. Si algo cambia, se actualiza este archivo mediante un PR.

## Convenciones generales

- Prefijo `/api/`. Todos los endpoints requieren el header `Authorization: Bearer <access_token>`.
- Sin token o con token vencido: **401**. Con un rol que no corresponde: **403**.
- Las fechas viajan en ISO 8601 y **en UTC** (`2026-11-20T13:00:00Z`). El frontend las muestra en hora de Argentina (`America/Argentina/Buenos_Aires`).
- Los importes viajan como texto con dos decimales (`"12500.00"`).
- Estados del turno: `pendiente`, `en_proceso`, `finalizado`, `entregado` y `cancelado`.
- Errores de validación (**400**): `{"campo": ["mensaje"]}`. Otros errores: `{"detail": "mensaje"}`.
- Los listados van paginados: `{"count": 0, "next": null, "previous": null, "results": []}`, con 20 elementos por página.

## Reglas de negocio que el contrato asume

1. **Horario de atención:** de 8:00 a 20:00 (hora de Argentina), definido como constante en `settings`. Un turno debe empezar y terminar dentro de ese horario.
2. **Asignación de box:** el cliente no elige el box. El backend asigna el primer box activo (por id) que esté libre entre el inicio y el fin.
3. **Cálculo:** `precio_total` es la suma de la tarifa de cada servicio según el tipo del vehículo, y `fin` es `inicio` más la suma de las duraciones de cada servicio según el tipo del vehículo.
4. **Superposición:** dos turnos no cancelados no pueden ocupar el mismo box a la vez. Si no hay ningún box libre, la respuesta es **409**.
5. **Flujo de estados:** `pendiente` → `en_proceso` → `finalizado` → `entregado`, sin saltos ni retrocesos. Solo se cancela un turno `pendiente`.

## Objeto Turno

```json
{
  "id": 12,
  "vehiculo": {"id": 3, "patente": "AB123CD", "tipo": "auto"},
  "box": {"id": 1, "nombre": "Box 1"},
  "inicio": "2026-11-20T13:00:00Z",
  "fin": "2026-11-20T14:15:00Z",
  "estado": "pendiente",
  "precio_total": "12500.00",
  "servicios": [
    {"id": 1, "nombre": "Lavado completo", "precio_aplicado": "9000.00"},
    {"id": 2, "nombre": "Encerado", "precio_aplicado": "3500.00"}
  ]
}
```

En los listados para administrador y operario se agrega `cliente: {"id": 5, "nombre": "Ana Gómez"}`.

---

## POST /api/turnos/

Reserva un turno. **Rol:** cliente.

**Entrada**

```json
{"vehiculo": 3, "servicios": [1, 2], "inicio": "2026-11-20T13:00:00Z"}
```

El cliente no envía `fin`, `precio_total` ni `box`: los calcula el backend.

**Salida 201:** el objeto Turno, con estado `pendiente`.

| Código | Cuándo |
|---|---|
| 400 | Falta un campo, la lista de `servicios` está vacía, el vehículo no es del cliente o está inactivo, un servicio está inactivo o no tiene tarifa para el tipo de vehículo, el `inicio` es pasado o el turno queda fuera del horario de atención |
| 401 | Sin sesión |
| 403 | El usuario no es cliente |
| 409 | No hay ningún box libre en ese horario |

## GET /api/turnos/

Lista los turnos. **Roles:** todos.

- Cliente: solo sus turnos.
- Administrador y operario: todos los turnos (es la base de la agenda).

**Parámetros opcionales:** `fecha` (`2026-11-20`, día en hora de Argentina), `box` (id) y `estado`. Orden por `inicio` ascendente.

**Salida 200:** listado paginado de objetos Turno.

| Código | Cuándo |
|---|---|
| 400 | Un filtro tiene un formato inválido |
| 401 | Sin sesión |

## GET /api/turnos/{id}/

Detalle de un turno. **Roles:** todos.

**Salida 200:** el objeto Turno.

| Código | Cuándo |
|---|---|
| 401 | Sin sesión |
| 404 | No existe, o es el turno de otro cliente |

## PATCH /api/turnos/{id}/estado/

Avanza el estado de un turno. **Roles:** administrador y operario.

**Entrada**

```json
{"estado": "en_proceso"}
```

Solo acepta el siguiente estado del flujo. Para cancelar se usa el endpoint de cancelación.

| Estado actual | Estado permitido |
|---|---|
| `pendiente` | `en_proceso` |
| `en_proceso` | `finalizado` |
| `finalizado` | `entregado` |
| `entregado`, `cancelado` | Ninguno |

**Salida 200:** el objeto Turno actualizado.

| Código | Cuándo |
|---|---|
| 400 | Transición no permitida. Mensaje de ejemplo: `{"estado": ["No se puede pasar de 'pendiente' a 'finalizado'. Permitido: 'en_proceso'."]}`. También si se envía `cancelado` |
| 401 | Sin sesión |
| 403 | El usuario es cliente |
| 404 | El turno no existe |

## POST /api/turnos/{id}/cancelar/

Cancela un turno pendiente. **Roles:** cliente (solo sus turnos), administrador y operario.

**Entrada:** sin cuerpo.

**Salida 200:** el objeto Turno con estado `cancelado`. El horario queda libre para nuevas reservas.

| Código | Cuándo |
|---|---|
| 400 | El turno no está `pendiente`. Ejemplo: `{"detail": "Solo se puede cancelar un turno pendiente."}` |
| 401 | Sin sesión |
| 404 | No existe, o es el turno de otro cliente |

## GET /api/resumen/

Resumen de actividad e ingresos de un período. **Rol:** administrador.

**Parámetros obligatorios:** `desde` y `hasta` (`2026-11-01`, ambos incluidos, en hora de Argentina). Se filtra por la fecha de `inicio` del turno.

**Salida 200**

```json
{
  "desde": "2026-11-01",
  "hasta": "2026-11-30",
  "turnos_por_estado": {
    "pendiente": 4,
    "en_proceso": 1,
    "finalizado": 6,
    "entregado": 20,
    "cancelado": 3
  },
  "ingresos_total": "385000.00"
}
```

Los ingresos suman el `precio_total` de los turnos `finalizado` y `entregado`. Los pendientes, en proceso y cancelados no cuentan.

| Código | Cuándo |
|---|---|
| 400 | Falta `desde` o `hasta`, el formato es inválido o `desde` es posterior a `hasta` |
| 401 | Sin sesión |
| 403 | El usuario no es administrador |