
const CLAVE_SESION = "lavadero_sesion";

function notificarCambioSesion() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event("lavadero:sesion"));
  }
}

export function guardarSesion(datos) {
  const sesion = {
    access: datos.access,
    refresh: datos.refresh,
    usuario: datos.usuario,
  };

  sessionStorage.setItem(CLAVE_SESION, JSON.stringify(sesion));
  notificarCambioSesion();
}

export function obtenerSesion() {
  if (typeof window === "undefined") return null;

  try {
    const datos = sessionStorage.getItem(CLAVE_SESION);
    return datos ? JSON.parse(datos) : null;
  } catch {
    return null;
  }
}

export function obtenerAccessToken() {
  return obtenerSesion()?.access ?? null;
}

export function actualizarAccessToken(access) {
  const sesion = obtenerSesion();

  if (!sesion) return;

  sessionStorage.setItem(
    CLAVE_SESION,
    JSON.stringify({ ...sesion, access })
  );

  notificarCambioSesion();
}

export function cerrarSesionLocal() {
  if (typeof window === "undefined") return;

  sessionStorage.removeItem(CLAVE_SESION);
  notificarCambioSesion();
}
