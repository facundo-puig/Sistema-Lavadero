# SISTEMA LAVADERO



## Inicio de sesión (HU-A2)

El sistema permite iniciar sesión mediante correo electrónico y contraseña.

**Endpoint:** `POST /api/auth/login/`

Cuando las credenciales son correctas, el backend devuelve dos tokens JWT (`access` y `refresh`) junto con los datos del usuario, incluido su rol.

El frontend utiliza `apiFetch` para comunicarse con la API y almacena provisionalmente la sesión en `sessionStorage` bajo la clave `lavadero_sesion`.

Las peticiones autenticadas incluyen el token de acceso en el encabezado `Authorization: Bearer <token>`.

Por el momento, los clientes son redirigidos a `/turnos/nuevo` y los administradores y operarios a `/`. Las rutas definitivas por rol quedan pendientes de integración.

El almacenamiento en `sessionStorage` es una solución provisional para el desarrollo y no protege los tokens frente a ataques XSS. La renovación de tokens y el cierre de sesión se implementarán en HU-A3.

**Pruebas realizadas:**
- Inicio de sesión correcto: HTTP 200.
- Contraseña incorrecta: HTTP 401.
- Usuario inactivo: HTTP 401.
- Tests automatizados con pytest.
- Integración comprobada entre Django y Next.js.