"use client";

// Fila de un turno en la agenda: hora, vehículo, cliente, servicios, estado y el botón que
// avanza al único estado siguiente válido (no hay botón si el turno ya terminó o se canceló).

import Boton from "@/components/Boton";
import EstadoBadge from "@/components/turnos/EstadoBadge";
import { TIPOS_VEHICULO, ACCION_AVANZAR, SIGUIENTE_ESTADO } from "@/lib/constantes";
import { formatearHora, formatearPrecio } from "@/lib/formatos";

export default function AgendaTurno({ turno, onAvanzar, avanzando }) {
    const siguiente = SIGUIENTE_ESTADO[turno.estado];

    return (
        <article className="flex flex-wrap items-center gap-x-6 gap-y-2 rounded-lg border border-gray-200 bg-white p-3 text-sm shadow-sm">
            <div className="w-28 shrink-0 font-medium">
                {formatearHora(turno.inicio)} a {formatearHora(turno.fin)}
            </div>

            <div className="min-w-40 flex-1">
                <p className="font-medium">
                    {turno.vehiculo.patente}{" "}
                    <span className="font-normal text-gray-600">
                        ({TIPOS_VEHICULO[turno.vehiculo.tipo]})
                    </span>
                </p>
                <p className="text-gray-600">{turno.cliente?.nombre}</p>
            </div>

            <p className="min-w-40 flex-1 text-gray-700">
                {turno.servicios.map((s) => s.nombre).join(", ")}
                <span className="block text-gray-600">{formatearPrecio(turno.precio_total)}</span>
            </p>

            <EstadoBadge estado={turno.estado} />

            <div className="w-28 shrink-0 text-right">
                {siguiente && (
                    <Boton
                        onClick={() => onAvanzar(turno, siguiente)}
                        cargando={avanzando}
                        textoCargando="Guardando..."
                    >
                        {ACCION_AVANZAR[turno.estado]}
                    </Boton>
                )}
            </div>
        </article>
    );
}