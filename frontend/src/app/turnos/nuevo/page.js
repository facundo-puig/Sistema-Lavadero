"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import Boton from "@/components/Boton";
import { Campo, MensajeError, propsDeControl } from "@/components/Campo";
import ServicioOpcion from "@/components/turnos/ServicioOpcion";
import TurnoDetalle from "@/components/turnos/TurnoDetalle";
import { ApiError, apiFetch } from "@/lib/api";
import { HORARIO_ATENCION, TIPOS_VEHICULO } from "@/lib/constantes";
import { formatearDuracion, formatearPrecio } from "@/lib/formatos";
import {
    aIsoUtc,
    calcularResumen,
    horaDeFin,
    horariosDeInicio,
    tarifaDe,
    validarReserva,
} from "@/lib/turnos";

const HORARIOS = horariosDeInicio();

// El backend nombra los campos distinto que el formulario: `inicio` se reparte entre fecha y hora.
const CAMPO_DEL_FORMULARIO = { vehiculo: "vehiculo", servicios: "servicios", inicio: "hora" };

export default function NuevoTurnoPage() {
    const [vehiculos, setVehiculos] = useState([]);
    const [servicios, setServicios] = useState([]);
    const [carga, setCarga] = useState("cargando"); // "cargando" | "lista" | "error"
    const [vehiculoId, setVehiculoId] = useState("");
    const [serviciosIds, setServiciosIds] = useState([]);
    const [fecha, setFecha] = useState("");
    const [hora, setHora] = useState("");
    const [errores, setErrores] = useState({});
    const [enviando, setEnviando] = useState(false);
    const [turnoCreado, setTurnoCreado] = useState(null);

    // La API ya devuelve solo los vehículos activos del cliente y los servicios activos.
    useEffect(() => {
        let cancelado = false;

        async function cargarDatos() {
            try {
                const [listaVehiculos, listaServicios] = await Promise.all([
                    apiFetch("/api/vehiculos/"),
                    apiFetch("/api/catalogo/"),
                ]);
                if (cancelado) return;
                setVehiculos(listaVehiculos.results);
                setServicios(listaServicios);
                setCarga("lista");
            } catch {
                if (!cancelado) setCarga("error");
            }
        }

        cargarDatos();
        return () => {
            cancelado = true;
        };
    }, []);

    const vehiculo = vehiculos.find((v) => v.id === Number(vehiculoId));
    const serviciosElegidos = servicios.filter((s) => serviciosIds.includes(s.id));
    const resumen = vehiculo ? calcularResumen(serviciosElegidos, vehiculo.tipo) : null;

    function limpiarError(campo) {
        setErrores((e) => ({ ...e, [campo]: undefined }));
    }

    function cambiarVehiculo(id) {
        setVehiculoId(id);
        const nuevo = vehiculos.find((v) => v.id === Number(id));
        // Si un servicio ya elegido no tiene tarifa para el nuevo tipo de vehículo, se quita.
        if (nuevo) {
            setServiciosIds((ids) =>
                ids.filter((sid) => {
                    const s = servicios.find((x) => x.id === sid);
                    return s && tarifaDe(s, nuevo.tipo);
                }),
            );
        }
        limpiarError("vehiculo");
        limpiarError("servicios");
    }

    function alternarServicio(id) {
        setServiciosIds((ids) =>
            ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id],
        );
        limpiarError("servicios");
        limpiarError("hora");
    }

    async function confirmar(evento) {
        evento.preventDefault();
        setTurnoCreado(null);

        const nuevosErrores = validarReserva({
            vehiculo,
            servicios: serviciosElegidos,
            fecha,
            hora,
        });
        setErrores(nuevosErrores);
        if (Object.keys(nuevosErrores).length > 0) {
            toast.warning("Revisá los datos del formulario.");
            return;
        }

        setEnviando(true);
        try {
            const turno = await apiFetch("/api/turnos/", {
                method: "POST",
                body: JSON.stringify({
                    vehiculo: vehiculo.id,
                    servicios: serviciosElegidos.map((s) => s.id),
                    inicio: aIsoUtc(fecha, hora),
                }),
            });
            setTurnoCreado(turno);
            toast.success("¡Turno reservado!");
            setVehiculoId("");
            setServiciosIds([]);
            setFecha("");
            setHora("");
        } catch (error) {
            if (error instanceof ApiError && error.status === 409) {
                toast.error("No hay ningún box libre en ese horario. Probá con otro horario.");
            } else if (error instanceof ApiError && error.status === 400) {
                // Errores de validación del backend: { campo: ["mensaje"] }.
                const delBackend = {};
                for (const [campo, mensajes] of Object.entries(error.data ?? {})) {
                    const destino = CAMPO_DEL_FORMULARIO[campo];
                    if (destino) delBackend[destino] = [].concat(mensajes)[0];
                }
                setErrores(delBackend);
                toast.error(
                    Object.keys(delBackend).length > 0
                        ? "Revisá los datos del formulario."
                        : error.message,
                );
            } else {
                toast.error(
                    error instanceof ApiError ? error.message : "Ocurrió un error inesperado.",
                );
            }
        } finally {
            setEnviando(false);
        }
    }

    return (
        <section>
            <h1 className="text-2xl font-semibold">Reservar turno</h1>
            <p className="mt-1 text-sm text-gray-600">
                Elegí tu vehículo, los servicios y el horario de inicio. El precio y la
                hora de fin se calculan solos. Atendemos de {HORARIO_ATENCION.desde} a{" "}
                {HORARIO_ATENCION.hasta}.
            </p>

            {turnoCreado && (
                <div
                    role="status"
                    className="mt-6 rounded-lg border border-green-300 bg-green-50 p-4"
                >
                    <h2 className="mb-2 font-semibold text-green-800">Turno reservado</h2>
                    <TurnoDetalle turno={turnoCreado} />
                    <Link href="/turnos" className="mt-3 inline-block text-sm font-medium text-blue-600">
                        Ver mis turnos
                    </Link>
                </div>
            )}

            {carga === "cargando" && <p className="mt-6 text-gray-600">Cargando...</p>}

            {carga === "error" && (
                <div role="alert" className="mt-6 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">
                    No se pudieron cargar tus vehículos y los servicios. Recargá la página para reintentar.
                </div>
            )}

            {carga === "lista" && vehiculos.length === 0 && (
                <div role="status" className="mt-6 rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                    Todavía no tenés vehículos registrados. Registrá uno en{" "}
                    <Link href="/vehiculos" className="font-medium underline">
                        Mis vehículos
                    </Link>{" "}
                    para poder reservar.
                </div>
            )}

            {carga === "lista" && servicios.length === 0 && (
                <div role="status" className="mt-6 rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                    Por ahora no hay servicios disponibles para reservar.
                </div>
            )}

            {carga === "lista" && (
                <form onSubmit={confirmar} noValidate className="mt-6 grid gap-6 lg:grid-cols-3">
                    <div className="space-y-5 lg:col-span-2">
                        <Campo id="vehiculo" etiqueta="Vehículo" error={errores.vehiculo}>
                            <select
                                {...propsDeControl("vehiculo", errores.vehiculo)}
                                value={vehiculoId}
                                onChange={(e) => cambiarVehiculo(e.target.value)}
                            >
                                <option value="">Elegí un vehículo…</option>
                                {vehiculos.map((v) => (
                                    <option key={v.id} value={v.id}>
                                        {v.patente} · {TIPOS_VEHICULO[v.tipo]}
                                    </option>
                                ))}
                            </select>
                        </Campo>

                        <fieldset aria-describedby={errores.servicios ? "servicios-error" : undefined}>
                            <legend className="text-sm font-medium">Servicios</legend>
                            {!vehiculo && (
                                <p className="mt-1 text-sm text-gray-500">
                                    Elegí un vehículo para ver los precios y duraciones.
                                </p>
                            )}
                            <ul className="mt-2 space-y-2">
                                {servicios.map((s) => (
                                    <li key={s.id}>
                                        <ServicioOpcion
                                            servicio={s}
                                            tipoVehiculo={vehiculo?.tipo}
                                            marcado={serviciosIds.includes(s.id)}
                                            onCambio={() => alternarServicio(s.id)}
                                        />
                                    </li>
                                ))}
                            </ul>
                            <MensajeError id="servicios-error" mensaje={errores.servicios} />
                        </fieldset>

                        <div className="grid gap-5 sm:grid-cols-2">
                            <Campo id="fecha" etiqueta="Fecha" error={errores.fecha}>
                                <input
                                    {...propsDeControl("fecha", errores.fecha)}
                                    type="date"
                                    value={fecha}
                                    onChange={(e) => {
                                        setFecha(e.target.value);
                                        limpiarError("fecha");
                                    }}
                                />
                            </Campo>

                            <Campo id="hora" etiqueta="Horario de inicio" error={errores.hora}>
                                <select
                                    {...propsDeControl("hora", errores.hora)}
                                    value={hora}
                                    onChange={(e) => {
                                        setHora(e.target.value);
                                        limpiarError("hora");
                                    }}
                                >
                                    <option value="">Elegí un horario…</option>
                                    {HORARIOS.map((h) => (
                                        <option key={h} value={h}>
                                            {h}
                                        </option>
                                    ))}
                                </select>
                            </Campo>
                        </div>
                    </div>

                    <aside className="lg:col-span-1">
                        <div className="rounded-lg border bg-white p-4 text-sm shadow-sm lg:sticky lg:top-6">
                            <h2 className="font-semibold">Resumen</h2>
                            {!resumen || serviciosElegidos.length === 0 ? (
                                <p className="mt-2 text-gray-600">
                                    Elegí un vehículo y al menos un servicio para ver el precio y la duración.
                                </p>
                            ) : (
                                <dl className="mt-3 space-y-2">
                                    <div className="flex justify-between gap-4">
                                        <dt className="text-gray-600">Servicios</dt>
                                        <dd className="text-right">{serviciosElegidos.length}</dd>
                                    </div>
                                    <div className="flex justify-between gap-4">
                                        <dt className="text-gray-600">Duración estimada</dt>
                                        <dd className="text-right">{formatearDuracion(resumen.duracionMin)}</dd>
                                    </div>
                                    {hora && (
                                        <div className="flex justify-between gap-4">
                                            <dt className="text-gray-600">Terminaría a las</dt>
                                            <dd className="text-right">{horaDeFin(hora, resumen.duracionMin)}</dd>
                                        </div>
                                    )}
                                    <div className="flex justify-between gap-4 border-t pt-2 text-base font-semibold">
                                        <dt>Total</dt>
                                        <dd>{formatearPrecio(resumen.precioTotal)}</dd>
                                    </div>
                                </dl>
                            )}
                            <p className="mt-3 text-xs text-gray-500">
                                Son valores estimados. El box lo asigna el sistema y el precio final se
                                confirma al reservar.
                            </p>
                            <Boton
                                type="submit"
                                cargando={enviando}
                                textoCargando="Reservando…"
                                className="mt-4 w-full"
                            >
                                Confirmar turno
                            </Boton>
                        </div>
                    </aside>
                </form>
            )}
        </section>
    );
}