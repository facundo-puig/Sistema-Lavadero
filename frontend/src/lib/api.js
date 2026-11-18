
import { obtenerAccessToken } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

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

export async function apiFetch(path, options = {}) {
  if (!API_URL) {
    throw new Error("Falta configurar NEXT_PUBLIC_API_URL");
  }

  const token = obtenerAccessToken();

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  let res;

  try {
    res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new ApiError(0, "No se pudo conectar con el servidor.");
  }

  if (res.status === 204) return null;

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    throw new ApiError(res.status, mensajeDeError(res.status, data), data);
  }

  return data;
}
