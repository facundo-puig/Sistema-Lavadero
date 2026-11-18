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




## Renovación y cierre de sesión (HU-A3)

El sistema permite renovar automáticamente el token de acceso y cerrar sesión.

**Endpoints:**
- `POST /api/auth/refresh/`: recibe un refresh válido y devuelve un nuevo access.
- `POST /api/auth/logout/`: requiere autenticación y recibe el refresh para incorporarlo a la blacklist.

En el frontend, `apiFetch` detecta respuestas HTTP 401 de peticiones autenticadas e intenta renovar el access utilizando el refresh almacenado en `sessionStorage`. Si la renovación funciona, actualiza el token y repite la petición original una sola vez.

Si el refresh es inválido o está vencido, elimina la sesión local y redirige al usuario a `/login` con una notificación.

El botón **Cerrar sesión** revoca el refresh en el backend y elimina los datos de sesión del navegador. El access emitido anteriormente puede seguir siendo válido hasta su vencimiento.

**Pruebas realizadas:**
- Refresh correcto: HTTP 200.
- Logout correcto: HTTP 204.
- Refresh revocado: HTTP 401.
- Renovación automática del access comprobada desde Next.js.
- Redirección al login comprobada ante refresh inválido.
- 106 tests del backend aprobados.