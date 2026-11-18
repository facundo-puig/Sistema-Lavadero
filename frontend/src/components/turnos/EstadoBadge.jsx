// Etiqueta de color con el estado de un turno.

import { ESTADOS_TURNO } from "@/lib/constantes";

const COLORES = {
    pendiente: "bg-amber-100 text-amber-800",
    en_proceso: "bg-blue-100 text-blue-800",
    finalizado: "bg-green-100 text-green-800",
    entregado: "bg-gray-200 text-gray-700",
    cancelado: "bg-red-100 text-red-800",
};

export default function EstadoBadge({ estado }) {
    return (
        <span
            className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${COLORES[estado] ?? "bg-gray-100 text-gray-700"}`}
        >
            {ESTADOS_TURNO[estado] ?? estado}
        </span>
    );
}