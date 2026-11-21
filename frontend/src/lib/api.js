
import {
  actualizarAccessToken,
  cerrarSesionLocal,
  obtenerAccessToken,
  obtenerSesion,
} from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

let renovacionPendiente = null;

export class ApiError extends Error {
  constructor(status, message, data) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

function mensajeDeError(status, data) {
  if (data && typeof data === "object" && "detail" in data) {
    return String(data.detail);
  }

  if (status === 400) return "Hay datos inválidos. Revisá el formulario.";
  if (status === 401) return "Credenciales incorrectas o sesión vencida.";
  if (status === 403) return "No tenés permiso para realizar esta acción.";
  if (status === 404) return "No se encontró el recurso solicitado.";
  if (status >= 500) return "Error del servidor. Intentá más tarde.";

  return "Ocurrió un error inesperado.";
}

async function realizarPeticion(path, options, token) {
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  try {
    return await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new ApiError(0, "No se pudo conectar con el servidor.");
  }
}

async function leerRespuesta(res) {
  if (res.status === 204) return null;

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    throw new ApiError(
      res.status,
      mensajeDeError(res.status, data),
      data
    );
  }

  return data;
}

function redirigirPorSesionVencida() {
  if (typeof window !== "undefined") {
    sessionStorage.setItem("lavadero_aviso", "sesion_expirada");
  }

  cerrarSesionLocal();

  if (typeof window !== "undefined") {
    window.location.replace("/login");
  }
} 


async function renovarAccessToken() {
  const refresh = obtenerSesion()?.refresh;

  if (!refresh) {
    redirigirPorSesionVencida();

    throw new ApiError(
      401,
      "Tu sesión venció. Iniciá sesión nuevamente."
    );
  }

  if (!renovacionPendiente) {
    renovacionPendiente = (async () => {
      const res = await realizarPeticion(
        "/api/auth/refresh/",
        {
          method: "POST",
          body: JSON.stringify({ refresh }),
        },
        null
      );

      if (res.status === 400 || res.status === 401) {
        redirigirPorSesionVencida();
      }

      const datos = await leerRespuesta(res);

      actualizarAccessToken(datos.access);

      return datos.access;
    })().finally(() => {
      renovacionPendiente = null;
    });
  }

  return renovacionPendiente;
}



export async function apiFetch(path, options = {}) {
  if (!API_URL) {
    throw new Error("Falta configurar NEXT_PUBLIC_API_URL");
  }

  const esLogin = path === "/api/auth/login/";
  const esRefresh = path === "/api/auth/refresh/";
  const esRegistro = path === "/api/auth/registro/";
  const esRutaPublicaAuth = esLogin || esRefresh || esRegistro;

  const token = esRutaPublicaAuth ? null : obtenerAccessToken();

  let res = await realizarPeticion(path, options, token);

  if (res.status === 401 && token && !esRutaPublicaAuth) {
    const nuevoAccess = await renovarAccessToken();

    res = await realizarPeticion(path, options, nuevoAccess);
  }

  return leerRespuesta(res);
}

export async function cerrarSesion() {
  const refresh = obtenerSesion()?.refresh;

  try {
    if (refresh) {
      await apiFetch("/api/auth/logout/", {
        method: "POST",
        body: JSON.stringify({ refresh }),
      });
    }
  } finally {
    cerrarSesionLocal();
  }
}
