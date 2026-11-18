
# Permisos por rol — HU-A4

Los endpoints protegidos utilizan las clases definidas en
`backend/usuarios/permisos.py`.

## Clases disponibles

| Clase | Administrador | Operario | Cliente |
|---|---|---|---|
| EsAdministrador | Sí | No | No |
| EsOperario | No | Sí | No |
| EsCliente | No | No | Sí |
| EsAdministradorOOperario | Sí | Sí | No |

## Uso en las vistas

```python
from usuarios.permisos import EsAdministradorOOperario

class AgendaView(APIView):
    permission_classes = [EsAdministradorOOperario]
```

## Matriz de funcionalidades

| Funcionalidad | Roles permitidos |
|---|---|
| Gestión de usuarios | Administrador |
| Servicios, tarifas y boxes | Administrador |
| Resumen de ingresos | Administrador |
| Agenda de turnos | Administrador y operario |
| Cambio de estado de turnos | Administrador y operario |
| Vehículos propios | Cliente |
| Reserva y listado de turnos propios | Cliente |
| Cancelación de turnos | Cliente (propios), administrador y operario |

## Respuestas HTTP

- 401: usuario sin autenticación válida.
- 403: usuario autenticado con rol no permitido.
- 404: recurso inexistente o perteneciente a otro cliente.

`IsAuthenticated` es el permiso predeterminado de DRF.

Los endpoints públicos deben declarar `AllowAny` explícitamente.

Los clientes solo pueden consultar sus propios recursos.
Además del permiso por rol, las vistas deben filtrar sus
querysets según el usuario autenticado.
```
