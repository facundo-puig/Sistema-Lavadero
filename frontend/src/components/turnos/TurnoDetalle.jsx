// Datos de un turno, con la forma del contrato (docs/api-turnos.md).
// Se usa en la confirmación de la reserva y sirve igual para "Mis turnos" y la agenda.
// Si el turno trae `cliente` (listados de administrador y operario), se muestra también.

import { ESTADOS_TURNO, TIPOS_VEHICULO } from "@/lib/constantes";
import { formatearFechaHora, formatearHora, formatearPrecio } from "@/lib/formatos";

export default function TurnoDetalle({ turno }) {
    return (
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
            {turno.cliente && (
                <>
                    <dt className="text-gray-600">Cliente</dt>
                    <dd>{turno.cliente.nombre}</dd>
                </>
            )}
            <dt className="text-gray-600">Vehículo</dt>
            <dd>
                {turno.vehiculo.patente} ({TIPOS_VEHICULO[turno.vehiculo.tipo]})
            </dd>
            <dt className="text-gray-600">Cuándo</dt>
            <dd>
                {formatearFechaHora(turno.inicio)} a {formatearHora(turno.fin)}
            </dd>
            <dt className="text-gray-600">Box</dt>
            <dd>{turno.box.nombre}</dd>
            <dt className="text-gray-600">Servicios</dt>
            <dd>{turno.servicios.map((s) => s.nombre).join(", ")}</dd>
            <dt className="text-gray-600">Total</dt>
            <dd className="font-semibold">{formatearPrecio(turno.precio_total)}</dd>
            <dt className="text-gray-600">Estado</dt>
            <dd>{ESTADOS_TURNO[turno.estado]}</dd>
        </dl>
    );
}