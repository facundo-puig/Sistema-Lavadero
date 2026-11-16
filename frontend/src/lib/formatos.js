// Funciones para mostrar precios, duraciones y fechas. Se usan en todas las pantallas de turnos.

import { ZONA_HORARIA } from "@/lib/constantes";

// "12500.00" -> "$ 12.500"
export function formatearPrecio(valor) {
    return new Intl.NumberFormat("es-AR", {
        style: "currency",
        currency: "ARS",
        maximumFractionDigits: 0,
    }).format(parseFloat(valor));
}

// 90 -> "1 h 30 min"
export function formatearDuracion(minutos) {
    const h = Math.floor(minutos / 60);
    const m = minutos % 60;
    if (h === 0) return `${m} min`;
    if (m === 0) return `${h} h`;
    return `${h} h ${m} min`;
}

// ISO en UTC -> "jueves, 10 de diciembre de 2026, 10:00 a. m." (hora de Argentina)
export function formatearFechaHora(iso) {
    return new Date(iso).toLocaleString("es-AR", {
        timeZone: ZONA_HORARIA,
        dateStyle: "full",
        timeStyle: "short",
    });
}

// ISO en UTC -> "11:30 a. m." (hora de Argentina)
export function formatearHora(iso) {
    return new Date(iso).toLocaleTimeString("es-AR", {
        timeZone: ZONA_HORARIA,
        hour: "2-digit",
        minute: "2-digit",
    });
}