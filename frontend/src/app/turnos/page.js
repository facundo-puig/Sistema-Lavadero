"use client";

// Mis turnos (HU-C2): lista paginada de los turnos del cliente, con la opción de cancelar
// los pendientes (HU-C3). Datos: GET /api/turnos/ y POST /api/turnos/{id}/cancelar/.

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import TurnoTarjeta from "@/components/turnos/TurnoTarjeta";
import { ApiError, apiFetch } from "@/lib/api";
import { obtenerSesion } from "@/lib/auth";

const POR_PAGINA = 20;

export default function MisTurnosPage() {
    const router = useRouter();

    const [usuario, setUsuario] = useState(null);
    const [pagina, setPagina] = useState(1);
    const [datos, setDatos] = useState(null); // respuesta paginada de la API
    const [error, setError] = useState("");
    const [cancelandoId, setCancelandoId] = useState(null);

    const cargar = useCallback(async (numero) => {
        setError("");
        try {
            setDatos(await apiFetch(`/api/turnos/?page=${numero}`));
        } catch (err) {
            // Si la sesión venció, apiFetch ya redirige al login.
            setError(err.message || "No se pudieron cargar tus turnos.");
        }
    }, []);

    useEffect(() => {
        const sesion = obtenerSesion();
        if (!sesion) {
            router.replace("/login");
            return;
        }
        // Se lee la sesión una sola vez al montar (sessionStorage no existe en el servidor).
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setUsuario(sesion.usuario);
        if (sesion.usuario.rol === "CLIENTE") cargar(pagina);
    }, [router, cargar, pagina]);

    async function cancelar(turno) {
        setCancelandoId(turno.id);
        try {
            const actualizado = await apiFetch(`/api/turnos/${turno.id}/cancelar/`, {
                method: "POST",
            });
            setDatos((previo) => ({
                ...previo,
                results: previo.results.map((t) => (t.id === actualizado.id ? actualizado : t)),
            }));
            toast.success("El turno se canceló. El horario quedó libre.");
        } catch (err) {
            toast.error(err.message || "No se pudo cancelar el turno.");
            // El estado pudo cambiar desde otro lado (por ejemplo, ya estaba en proceso).
            if (err instanceof ApiError && err.status === 400) cargar(pagina);
        } finally {
            setCancelandoId(null);
        }
    }

    function irAPagina(numero) {
        setDatos(null);
        setPagina(numero);
    }

    if (!usuario) return null;

    if (usuario.rol !== "CLIENTE") {
        return (
            <section>
                <h1 className="text-2xl font-semibold">Turnos</h1>
                <p className="mt-2 text-gray-600">
                    Esta pantalla es para clientes. La agenda del personal todavía no está disponible.
                </p>
            </section>
        );
    }

    const total = datos?.count ?? 0;
    const totalPaginas = Math.max(1, Math.ceil(total / POR_PAGINA));

    return (
        <section>
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <h1 className="text-2xl font-semibold">Mis turnos</h1>
                <Link
                    href="/turnos/nuevo"
                    className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                    Reservar turno
                </Link>
            </div>

            {error && (
                <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">
                    <p>{error}</p>
                    <button
                        type="button"
                        onClick={() => cargar(pagina)}
                        className="mt-2 font-medium underline"
                    >
                        Reintentar
                    </button>
                </div>
            )}

            {!error && !datos && <p className="text-gray-600">Cargando tus turnos...</p>}

            {datos && datos.results.length === 0 && (
                <div className="rounded-lg border border-dashed border-gray-300 bg-white p-8 text-center">
                    <p className="text-gray-700">Todavía no reservaste ningún turno.</p>
                    <Link href="/turnos/nuevo" className="mt-2 inline-block font-medium text-blue-600">
                        Reservar mi primer turno
                    </Link>
                </div>
            )}

            {datos && datos.results.length > 0 && (
                <>
                    <ul className="space-y-4">
                        {datos.results.map((turno) => (
                            <li key={turno.id}>
                                <TurnoTarjeta
                                    turno={turno}
                                    onCancelar={cancelar}
                                    cancelando={cancelandoId === turno.id}
                                />
                            </li>
                        ))}
                    </ul>

                    {totalPaginas > 1 && (
                        <nav className="mt-6 flex items-center justify-between" aria-label="Paginación">
                            <button
                                type="button"
                                onClick={() => irAPagina(pagina - 1)}
                                disabled={!datos.previous}
                                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-100 disabled:opacity-40"
                            >
                                Anterior
                            </button>
                            <span className="text-sm text-gray-600">
                                Página {pagina} de {totalPaginas}
                            </span>
                            <button
                                type="button"
                                onClick={() => irAPagina(pagina + 1)}
                                disabled={!datos.next}
                                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-100 disabled:opacity-40"
                            >
                                Siguiente
                            </button>
                        </nav>
                    )}
                </>
            )}
        </section>
    );
}