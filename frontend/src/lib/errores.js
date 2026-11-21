// Convierte los errores de la API en texto para mostrar en pantalla.

// {"campo": ["mensaje"]} (o listas y objetos anidados) -> "mensaje".
export function textoDeError(valor) {
  if (Array.isArray(valor)) {
    return valor.map(textoDeError).filter(Boolean).join(" ");
  }

  if (valor && typeof valor === "object") {
    return Object.values(valor).map(textoDeError).filter(Boolean).join(" ");
  }

  return String(valor);
}

// Devuelve un mensaje por campo. Los errores sin campo ({"detail": ...}) quedan en "general".
export function erroresDeApi(error) {
  const datos = error.data;

  if (!datos || typeof datos !== "object" || Array.isArray(datos)) {
    return { general: error.message };
  }

  const errores = {};

  for (const [campo, valor] of Object.entries(datos)) {
    errores[campo === "detail" ? "general" : campo] = textoDeError(valor);
  }

  return errores;
}
