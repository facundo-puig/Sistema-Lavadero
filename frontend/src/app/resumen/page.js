"use client";

// Resumen (HU-C6): cantidad de turnos por estado e ingresos de un período.
// Datos: GET /api/resumen/?desde=...&hasta=... (solo administrador).

import { useEffect, useState } from "react";

import EstadoBadge from "@/components/turnos/EstadoBadge";
import { apiFetch } from "@/lib/api";
import { ESTADOS_TURNO, ZONA_HORARIA } from "@/lib/constantes";
import { formatearPrecio } from "@/lib/formatos";

// Primer día del mes y hoy, en hora de Argentina, como "2026-11-01".
function periodoInicial() {
    const hoy = new Date().toLocaleDateString("en-CA", { timeZone: ZONA_HORARIA });
    return { desde: `${hoy.slice(0, 8)}01`, hasta: hoy };
}

const ESTILO_FECHA =
    "mt-1 block rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500";

export default function ResumenPage() {
    const [periodo, setPeriodo] = useState(periodoInicial);
    const [datos, setDatos] = useState(null);
    const [error, setError] = useState("");

    const { desde, hasta } = periodo;
    const errorDePeriodo =
        !desde || !hasta
            ? "Elegí las dos fechas."
            : desde > hasta
                ? "La fecha desde no puede ser posterior a la fecha hasta."
                : "";

    useEffect(() => {
        if (errorDePeriodo) return;
        let vigente = true;
        // Si se cambia el período mientras carga, se descarta la respuesta vieja.
        apiFetch(`/api/resumen/?desde=${desde}&hasta=${hasta}`)
            .then((respuesta) => {
                if (vigente) {
                    setError("");
                    setDatos(respuesta);
                }
            })
            .catch((err) => {
                if (vigente) setError(err.message || "No se pudo cargar el resumen.");
            });
        return () => {
            vigente = false;
        };
    }, [desde, hasta, errorDePeriodo]);

    const totalTurnos = datos
        ? Object.values(datos.turnos_por_estado).reduce((suma, n) => suma + n, 0)
        : 0;

    return (
        <section>
            <h1 className="text-2xl font-semibold">Resumen</h1>
            <p className="mt-1 text-sm text-gray-600">
                Turnos por estado e ingresos del período. Los ingresos suman los turnos
                finalizados y entregados.
            </p>

            <div className="mt-4 flex flex-wrap items-end gap-3">
                <label className="text-sm font-medium">
                    Desde
                    <input
                        type="date"
                        value={desde}
                        onChange={(e) => setPeriodo({ ...periodo, desde: e.target.value })}
                        className={ESTILO_FECHA}
                    />
                </label>
                <label className="text-sm font-medium">
                    Hasta
                    <input
                        type="date"
                        value={hasta}
                        onChange={(e) => setPeriodo({ ...periodo, hasta: e.target.value })}
                        className={ESTILO_FECHA}
                    />
                </label>
            </div>

            {errorDePeriodo && (
                <p role="alert" className="mt-3 text-sm text-red-600">
                    {errorDePeriodo}
                </p>
            )}

            {!errorDePeriodo && error && (
                <div role="alert" className="mt-6 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">
                    {error}
                </div>
            )}

            {!errorDePeriodo && !error && !datos && (
                <p className="mt-6 text-gray-600">Cargando el resumen...</p>
            )}

            {!errorDePeriodo && !error && datos && (
                <div className="mt-6 space-y-6">
                    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                        <p className="text-sm text-gray-600">Ingresos del período</p>
                        <p className="mt-1 text-3xl font-semibold">
                            {formatearPrecio(datos.ingresos_total)}
                        </p>
                    </div>

                    <div>
                        <h2 className="mb-2 font-semibold">
                            Turnos por estado{" "}
                            <span className="text-sm font-normal text-gray-600">
                                ({totalTurnos} en total)
                            </span>
                        </h2>
                        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                            {Object.keys(ESTADOS_TURNO).map((estado) => (
                                <li
                                    key={estado}
                                    className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
                                >
                                    <EstadoBadge estado={estado} />
                                    <p className="mt-2 text-2xl font-semibold">
                                        {datos.turnos_por_estado[estado] ?? 0}
                                    </p>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {totalTurnos === 0 && (
                        <p className="text-sm text-gray-600">No hay turnos en este período.</p>
                    )}
                </div>
            )}
        </section>
    );
}