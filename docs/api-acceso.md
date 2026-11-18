
# API de Acceso — Sistema Lavadero

## Convenciones generales

- Prefijo de la API: `/api/`
- Formato de entrada y salida: JSON.
- La autenticación utiliza JWT.
- Las rutas públicas no requieren autenticación.
- Las rutas protegidas utilizan `Authorization: Bearer <access>`.
- Los roles disponibles son `ADMINISTRADOR`, `OPERARIO` y `CLIENTE`.



## HU-A1 — Registro de clientes

### POST /api/auth/registro/

Permite registrar un nuevo cliente utilizando nombre, email y contraseña.

**Acceso:** Público (`AllowAny`).

### Entrada

```json
{
  "nombre": "Juan",
  "email": "juan@example.com",
  "password": "ClaveSegura123!"
}
```

### Respuesta exitosa — HTTP 201

```json
{
  "id": 1,
  "nombre": "Juan",
  "email": "juan@example.com",
  "rol": "CLIENTE"
}
```

El rol se asigna automáticamente como `CLIENTE`, aunque se envíe otro rol en la solicitud.

### Errores

| Código | Descripción |
|---|---|
| 400 | Faltan campos o tienen un formato inválido |
| 400 | El email ya está registrado |
| 400 | La contraseña no cumple las validaciones de seguridad |

Los errores de validación se devuelven indicando el campo correspondiente, por ejemplo `email` o `password`.

### Seguridad

- La contraseña se almacena utilizando el sistema de hashing de Django.
- La contraseña nunca aparece en la respuesta.
- El registro público no permite crear administradores ni operarios.
- Los emails se normalizan a minúsculas antes de guardarse.

---



## HU-A2 — Inicio de sesión

### POST /api/auth/login/

Permite iniciar sesión utilizando email y contraseña.

**Acceso:** Público (`AllowAny`).

### Entrada

```json
{
  "email": "cliente@ejemplo.com",
  "password": "contraseña"
}
```

### Respuesta exitosa — HTTP 200

```json
{
  "access": "token_jwt_de_acceso",
  "refresh": "token_jwt_de_actualizacion",
  "usuario": {
    "id": 1,
    "email": "cliente@ejemplo.com",
    "rol": "CLIENTE"
  }
}
```

El frontend utiliza el rol para redirigir al usuario a la pantalla correspondiente.

### Errores

| Código | Descripción |
|---|---|
| 400 | Faltan campos o los datos tienen un formato inválido |
| 401 | Email o contraseña incorrectos |
| 401 | Usuario inactivo |

El sistema no revela si un email existe al devolver un error de autenticación.

### Seguridad

- Las contraseñas nunca se devuelven en las respuestas.
- Los tokens se generan utilizando SimpleJWT.
- El almacenamiento del token en el frontend se documentará en el README.
