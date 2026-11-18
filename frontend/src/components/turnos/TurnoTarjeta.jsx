"use client";

// Tarjeta de un turno en "Mis turnos". Si el turno está pendiente, permite cancelarlo
// pidiendo una confirmación antes (la cancelación no se puede deshacer).

import { useState } from "react";

import Boton from "@/components/Boton";
import EstadoBadge from "@/components/turnos/EstadoBadge";
import TurnoDetalle from "@/components/turnos/TurnoDetalle";
import { formatearFechaHora } from "@/lib/formatos";

export default function TurnoTarjeta({ turno, onCancelar, cancelando }) {
    const [confirmando, setConfirmando] = useState(false);

    async function confirmar() {
        await onCancelar(turno);
        setConfirmando(false);
    }

    return (
        <article className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <header className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-medium first-letter:uppercase">{formatearFechaHora(turno.inicio)}</h2>
                <EstadoBadge estado={turno.estado} />
            </header>

            <TurnoDetalle turno={turno} />

            {turno.estado === "pendiente" && (
                <footer className="mt-4 border-t border-gray-100 pt-3">
                    {!confirmando ? (
                        <button
                            type="button"
                            onClick={() => setConfirmando(true)}
                            className="rounded-md border border-red-300 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50"
                        >
                            Cancelar turno
                        </button>
                    ) : (
                        <div className="flex flex-wrap items-center gap-3" role="alert">
                            <span className="text-sm">
                                ¿Seguro que querés cancelar este turno?
                            </span>
                            <Boton
                                onClick={confirmar}
                                cargando={cancelando}
                                textoCargando="Cancelando..."
                                className="!bg-red-600 hover:!bg-red-700 focus:!ring-red-500"
                            >
                                Sí, cancelar
                            </Boton>
                            <button
                                type="button"
                                onClick={() => setConfirmando(false)}
                                disabled={cancelando}
                                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-100 disabled:opacity-60"
                            >
                                No, volver
                            </button>
                        </div>
                    )}
                </footer>
            )}
        </article>
    );
}