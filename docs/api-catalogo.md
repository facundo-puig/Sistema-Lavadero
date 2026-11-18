# API del catálogo

Contrato de los endpoints del bloque de catálogo: servicios con sus tarifas, boxes, vehículos del cliente y catálogo para reservar. Define qué envía y qué devuelve cada endpoint, para que el backend y el frontend se trabajen en paralelo. Si algo cambia, se actualiza este archivo mediante un PR.

## Convenciones generales

- Prefijo `/api/`. Todos los endpoints requieren el header `Authorization: Bearer <access_token>`.
- Sin token o con token vencido: **401**. Con un rol que no corresponde: **403**.
- Los importes viajan como texto con dos decimales (`"9000.00"`).
- Tipos de vehículo: `auto`, `camioneta` y `moto`.
- Errores de validación (**400**): `{"campo": ["mensaje"]}`. Otros errores: `{"detail": "mensaje"}`.
- Los listados van paginados: `{"count": 0, "next": null, "previous": null, "results": []}`, con 20 elementos por página. La excepción es `GET /api/catalogo/`, que devuelve la lista completa.
- `DELETE` hace baja lógica (`activo=false`) y nunca borra la fila. Responde **204** sin cuerpo, también si el registro ya estaba inactivo.

## Permisos

| Endpoint | Administrador | Operario | Cliente |
|---|---|---|---|
| `/api/servicios/` (todos los métodos) | Sí | No | No |
| `/api/boxes/` (todos los métodos) | Sí | No | No |
| `/api/vehiculos/` (todos los métodos) | No | No | Sí |
| `GET /api/catalogo/` | No | No | Sí |

Se usan las clases de `usuarios.permisos` (`EsAdministrador`, `EsCliente`). Un cliente solo ve y modifica sus propios vehículos: los ajenos devuelven **404**.

## Objetos

### Tarifa (siempre anidada en un servicio)

```json
{
  "id": 1,
  "tipo_vehiculo": "auto",
  "precio": "12500.00",
  "duracion_minutos": 45
}
```

Reglas: `precio` mayor a 0, `duracion_minutos` mayor a 0 y una sola tarifa por servicio y tipo de vehículo.

### Servicio

```json
{
  "id": 3,
  "nombre": "Lavado completo",
  "descripcion": "Exterior, interior y aspirado.",
  "activo": true,
  "tarifas": [
    {"id": 1, "tipo_vehiculo": "auto", "precio": "12500.00", "duracion_minutos": 45},
    {"id": 2, "tipo_vehiculo": "camioneta", "precio": "16000.00", "duracion_minutos": 60}
  ]
}
```

### Box

```json
{"id": 1, "nombre": "Box 1", "activo": true}
```

### Vehículo

```json
{"id": 7, "patente": "ABC123", "tipo": "auto", "activo": true}
```

La patente se normaliza antes de guardar: mayúsculas, sin espacios ni guiones (`"ab-c 123"` se guarda como `"ABC123"`). Se valida el formato (`ABC123`, `AB123CD`, `123ABC` o `A123BCD`) y es única en todo el sistema, incluso entre vehículos inactivos.

## GET /api/catalogo/

Catálogo para reservar (HU-B5). Solo lectura.

- **Rol:** cliente.
- **Entrada:** ninguna.
- **Salida 200:** lista completa, sin paginar, de los servicios **activos** ordenada por `nombre`, cada uno con sus tarifas. Un servicio sin tarifas se devuelve con `"tarifas": []`.

```json
[
  {
    "id": 3,
    "nombre": "Lavado completo",
    "descripcion": "Exterior, interior y aspirado.",
    "tarifas": [
      {"id": 1, "tipo_vehiculo": "auto", "precio": "12500.00", "duracion_minutos": 45}
    ]
  }
]
```

| Código | Cuándo |
|---|---|
| 401 | Sin sesión |
| 403 | El usuario no es cliente |

## GET /api/vehiculos/

Lista los vehículos **activos** del cliente autenticado (HU-B4).

- **Rol:** cliente.
- **Salida 200:** listado paginado de objetos Vehículo.

| Código | Cuándo |
|---|---|
| 401 | Sin sesión |
| 403 | El usuario no es cliente |

## POST /api/vehiculos/

Registra un vehículo del cliente autenticado.

- **Rol:** cliente.
- **Entrada:** `patente` y `tipo`. El dueño es siempre el usuario de la sesión; no se acepta un campo de cliente.
- **Salida 201:** objeto Vehículo con la patente normalizada.

```json
{"patente": "ab 123-cd", "tipo": "camioneta"}
```

| Código | Cuándo |
|---|---|
| 400 | Patente faltante, con formato inválido o ya registrada; `tipo` inexistente |
| 401 | Sin sesión |
| 403 | El usuario no es cliente |

## GET /api/vehiculos/{id}/

- **Rol:** cliente.
- **Salida 200:** objeto Vehículo propio.

| Código | Cuándo |
|---|---|
| 401 | Sin sesión |
| 403 | El usuario no es cliente |
| 404 | No existe o pertenece a otro cliente |

## PUT y PATCH /api/vehiculos/{id}/

Edita `patente` y `tipo` de un vehículo propio. `PUT` exige ambos campos; `PATCH` acepta cualquiera de los dos. La patente se normaliza igual que al crear.

- **Rol:** cliente.
- **Salida 200:** objeto Vehículo actualizado.

| Código | Cuándo |
|---|---|
| 400 | Patente con formato inválido o ya registrada por otro vehículo; `tipo` inexistente |
| 401 | Sin sesión |
| 403 | El usuario no es cliente |
| 404 | No existe o pertenece a otro cliente |

## DELETE /api/vehiculos/{id}/

Baja lógica de un vehículo propio (`activo=false`). Los turnos que ya lo referencian se conservan.

- **Rol:** cliente.
- **Salida 204:** sin cuerpo.

| Código | Cuándo |
|---|---|
| 401 | Sin sesión |
| 403 | El usuario no es cliente |
| 404 | No existe o pertenece a otro cliente |

## GET /api/servicios/

Lista los servicios con sus tarifas (HU-B1 y HU-B2).

- **Rol:** administrador.
- **Filtro opcional:** `?activo=true` o `?activo=false`.
- **Salida 200:** listado paginado de objetos Servicio.

| Código | Cuándo |
|---|---|
| 401 | Sin sesión |
| 403 | El usuario no es administrador |

## POST /api/servicios/

Crea un servicio junto con sus tarifas.

- **Rol:** administrador.
- **Entrada:** `nombre`, `descripcion` (opcional) y `tarifas`, una lista con `tipo_vehiculo`, `precio` y `duracion_minutos` (sin repetir tipo). `activo` queda en `true`.
- **Salida 201:** objeto Servicio.

```json
{
  "nombre": "Lavado completo",
  "descripcion": "Exterior, interior y aspirado.",
  "tarifas": [
    {"tipo_vehiculo": "auto", "precio": "12500.00", "duracion_minutos": 45},
    {"tipo_vehiculo": "moto", "precio": "6000.00", "duracion_minutos": 25}
  ]
}
```

| Código | Cuándo |
|---|---|
| 400 | Nombre faltante, precio o duración menores o iguales a 0, `tipo_vehiculo` inexistente o repetido en la lista |
| 401 | Sin sesión |
| 403 | El usuario no es administrador |

## GET /api/servicios/{id}/

- **Rol:** administrador.
- **Salida 200:** objeto Servicio.

| Código | Cuándo |
|---|---|
| 401 | Sin sesión |
| 403 | El usuario no es administrador |
| 404 | No existe |

## PUT y PATCH /api/servicios/{id}/

Edita un servicio. `PUT` exige `nombre`; `PATCH` acepta cualquier campo (`nombre`, `descripcion`, `activo`, `tarifas`).

Si se envía `tarifas`, cada elemento se **crea o actualiza** según su `tipo_vehiculo`; los tipos que no se envían quedan como están. Si no se envía, las tarifas no cambian. Las tarifas no se eliminan: para dejar de ofrecer un servicio se lo da de baja.

- **Rol:** administrador.
- **Salida 200:** objeto Servicio actualizado.

| Código | Cuándo |
|---|---|
| 400 | Mismos casos que en el alta |
| 401 | Sin sesión |
| 403 | El usuario no es administrador |
| 404 | No existe |

## DELETE /api/servicios/{id}/

Baja lógica (`activo=false`). Los turnos que ya lo referencian se conservan.

- **Rol:** administrador.
- **Salida 204:** sin cuerpo.

| Código | Cuándo |
|---|---|
| 401 | Sin sesión |
| 403 | El usuario no es administrador |
| 404 | No existe |

## /api/boxes/

Gestión de boxes (HU-B3). Solo administrador.

| Método y ruta | Descripción | Salida |
|---|---|---|
| `GET /api/boxes/` | Lista los boxes. Filtro opcional `?activo=true` o `?activo=false` | 200, paginado |
| `POST /api/boxes/` | Crea un box. Entrada: `nombre` | 201, objeto Box |
| `GET /api/boxes/{id}/` | Detalle | 200, objeto Box |
| `PUT` y `PATCH /api/boxes/{id}/` | Edita `nombre` y `activo` (`PUT` exige `nombre`) | 200, objeto Box |
| `DELETE /api/boxes/{id}/` | Baja lógica | 204 |

| Código | Cuándo |
|---|---|
| 400 | Nombre faltante o inválido |
| 401 | Sin sesión |
| 403 | El usuario no es administrador |
| 404 | No existe |
