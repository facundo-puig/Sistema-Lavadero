
const CLAVE_SESION = "lavadero_sesion";

export function guardarSesion(datos) {
  const sesion = {
    access: datos.access,
    refresh: datos.refresh,
    usuario: datos.usuario,
  };

  sessionStorage.setItem(CLAVE_SESION, JSON.stringify(sesion));
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

export function cerrarSesionLocal() {
  sessionStorage.removeItem(CLAVE_SESION);
}
