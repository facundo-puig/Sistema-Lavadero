"use client";

// Agenda (HU-C4 y HU-C5): los turnos de un día agrupados por box, con filtros y los botones
// para avanzar el estado. Datos: GET /api/turnos/?fecha=... y PATCH /api/turnos/{id}/estado/.

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import AgendaTurno from "@/components/turnos/AgendaTurno";
import { ApiError, apiFetch } from "@/lib/api";
import { ESTADOS_TURNO, ZONA_HORARIA } from "@/lib/constantes";

// Fecha de hoy en Argentina como "2026-11-20" (el formato en-CA da año-mes-día).
function hoyEnArgentina() {
    return new Date().toLocaleDateString("en-CA", { timeZone: ZONA_HORARIA });
}

// Suma (o resta) días a una fecha "2026-11-20".
function sumarDias(fecha, dias) {
    const d = new Date(`${fecha}T12:00:00Z`);
    d.setUTCDate(d.getUTCDate() + dias);
    return d.toISOString().slice(0, 10);
}

function tituloDelDia(fecha) {
    return new Date(`${fecha}T12:00:00Z`).toLocaleDateString("es-AR", {
        timeZone: "UTC",
        dateStyle: "full",
    });
}

// Trae todas las páginas del día (la API pagina de a 20).
async function traerTurnosDelDia(fecha) {
    const todos = [];
    for (let pagina = 1; ; pagina++) {
        const datos = await apiFetch(`/api/turnos/?fecha=${fecha}&page=${pagina}`);
        todos.push(...datos.results);
        if (!datos.next) return todos;
    }
}

export default function AgendaPage() {
    const [fecha, setFecha] = useState(hoyEnArgentina);
    const [turnos, setTurnos] = useState(null);
    const [error, setError] = useState("");
    const [filtroBox, setFiltroBox] = useState("");
    const [filtroEstado, setFiltroEstado] = useState("");
    const [avanzandoId, setAvanzandoId] = useState(null);

    const cargar = useCallback(async (dia) => {
        setError("");
        try {
            setTurnos(await traerTurnosDelDia(dia));
        } catch (err) {
            setError(err.message || "No se pudo cargar la agenda.");
        }
    }, []);

    useEffect(() => {
        let vigente = true;
        // Si se cambia de día mientras carga, se descarta la respuesta vieja.
        traerTurnosDelDia(fecha)
            .then((lista) => {
                if (vigente) {
                    setError("");
                    setTurnos(lista);
                }
            })
            .catch((err) => {
                if (vigente) setError(err.message || "No se pudo cargar la agenda.");
            });
        return () => {
            vigente = false;
        };
    }, [fecha]);

    function cambiarFecha(nueva) {
        if (!nueva) return;
        setTurnos(null);
        setFiltroBox("");
        setFecha(nueva);
    }

    async function avanzar(turno, siguiente) {
        setAvanzandoId(turno.id);
        try {
            const actualizado = await apiFetch(`/api/turnos/${turno.id}/estado/`, {
                method: "PATCH",
                body: JSON.stringify({ estado: siguiente }),
            });
            // La respuesta de este endpoint no trae el cliente: se conserva el que ya teníamos.
            setTurnos((previo) =>
                previo.map((t) =>
                    t.id === turno.id ? { ...actualizado, cliente: t.cliente } : t,
                ),
            );
            toast.success(`Turno ${ESTADOS_TURNO[siguiente].toLowerCase()}.`);
        } catch (err) {
            toast.error(err.message || "No se pudo cambiar el estado.");
            // Otro usuario pudo haber movido el turno: se recarga para mostrar lo real.
            if (err instanceof ApiError && err.status === 400) cargar(fecha);
        } finally {
            setAvanzandoId(null);
        }
    }

    // Los boxes del filtro salen de los turnos del día. Los filtros se aplican en el navegador
    // sobre el día ya cargado.
    const boxes = useMemo(() => {
        const porId = new Map();
        for (const t of turnos ?? []) porId.set(t.box.id, t.box);
        return [...porId.values()].sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));
    }, [turnos]);

    const visibles = (turnos ?? []).filter(
        (t) =>
            (!filtroBox || String(t.box.id) === filtroBox) &&
            (!filtroEstado || t.estado === filtroEstado),
    );

    const porBox = boxes
        .map((box) => ({ box, lista: visibles.filter((t) => t.box.id === box.id) }))
        .filter((grupo) => grupo.lista.length > 0);

    const controlBase =
        "rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500";

    return (
        <section>
            <h1 className="text-2xl font-semibold">Agenda</h1>
            <p className="mt-1 text-sm text-gray-600 first-letter:uppercase">{tituloDelDia(fecha)}</p>

            <div className="mt-4 flex flex-wrap items-end gap-3">
                <div className="flex items-end gap-1">
                    <button
                        type="button"
                        onClick={() => cambiarFecha(sumarDias(fecha, -1))}
                        aria-label="Día anterior"
                        className={controlBase}
                    >
                        ‹
                    </button>
                    <label className="text-sm font-medium">
                        Fecha
                        <input
                            type="date"
                            value={fecha}
                            onChange={(e) => cambiarFecha(e.target.value)}
                            className={`${controlBase} mt-1 block`}
                        />
                    </label>
                    <button
                        type="button"
                        onClick={() => cambiarFecha(sumarDias(fecha, 1))}
                        aria-label="Día siguiente"
                        className={controlBase}
                    >
                        ›
                    </button>
                    <button
                        type="button"
                        onClick={() => cambiarFecha(hoyEnArgentina())}
                        className={controlBase}
                    >
                        Hoy
                    </button>
                </div>

                <label className="text-sm font-medium">
                    Box
                    <select
                        value={filtroBox}
                        onChange={(e) => setFiltroBox(e.target.value)}
                        className={`${controlBase} mt-1 block`}
                    >
                        <option value="">Todos</option>
                        {boxes.map((b) => (
                            <option key={b.id} value={b.id}>
                                {b.nombre}
                            </option>
                        ))}
                    </select>
                </label>

                <label className="text-sm font-medium">
                    Estado
                    <select
                        value={filtroEstado}
                        onChange={(e) => setFiltroEstado(e.target.value)}
                        className={`${controlBase} mt-1 block`}
                    >
                        <option value="">Todos</option>
                        {Object.entries(ESTADOS_TURNO).map(([valor, texto]) => (
                            <option key={valor} value={valor}>
                                {texto}
                            </option>
                        ))}
                    </select>
                </label>
            </div>

            <div className="mt-6">
                {error && (
                    <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">
                        <p>{error}</p>
                        <button type="button" onClick={() => cargar(fecha)} className="mt-2 font-medium underline">
                            Reintentar
                        </button>
                    </div>
                )}

                {!error && !turnos && <p className="text-gray-600">Cargando la agenda...</p>}

                {turnos && turnos.length === 0 && (
                    <div className="rounded-lg border border-dashed border-gray-300 bg-white p-8 text-center text-gray-700">
                        No hay turnos para este día.
                    </div>
                )}

                {turnos && turnos.length > 0 && visibles.length === 0 && (
                    <div className="rounded-lg border border-dashed border-gray-300 bg-white p-8 text-center text-gray-700">
                        Ningún turno coincide con los filtros.
                    </div>
                )}

                <div className="space-y-6">
                    {porBox.map(({ box, lista }) => (
                        <section key={box.id} aria-labelledby={`box-${box.id}`}>
                            <h2 id={`box-${box.id}`} className="mb-2 font-semibold">
                                {box.nombre}{" "}
                                <span className="text-sm font-normal text-gray-600">
                                    ({lista.length} {lista.length === 1 ? "turno" : "turnos"})
                                </span>
                            </h2>
                            <ul className="space-y-2">
                                {lista.map((turno) => (
                                    <li key={turno.id}>
                                        <AgendaTurno
                                            turno={turno}
                                            onAvanzar={avanzar}
                                            avanzando={avanzandoId === turno.id}
                                        />
                                    </li>
                                ))}
                            </ul>
                        </section>
                    ))}
                </div>
            </div>
        </section>
    );
}