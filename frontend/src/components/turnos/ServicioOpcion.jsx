// Tarjeta con checkbox para elegir un servicio al reservar.
// Muestra el precio y la duración según el tipo de vehículo. Queda deshabilitada si todavía
// no se eligió vehículo o si el servicio no tiene tarifa para ese tipo.

import { TIPOS_VEHICULO } from "@/lib/constantes";
import { formatearDuracion, formatearPrecio } from "@/lib/formatos";
import { tarifaDe } from "@/lib/turnos";

export default function ServicioOpcion({ servicio, tipoVehiculo, marcado, onCambio }) {
    const tarifa = tipoVehiculo ? tarifaDe(servicio, tipoVehiculo) : null;
    const sinTarifa = Boolean(tipoVehiculo) && !tarifa;

    return (
        <label
            className={`flex items-start gap-3 rounded-md border bg-white p-3 text-sm ${sinTarifa ? "cursor-not-allowed opacity-50" : "cursor-pointer"
                } ${marcado ? "border-blue-500 ring-1 ring-blue-500" : "border-gray-300"}`}
        >
            <input
                type="checkbox"
                checked={marcado}
                disabled={!tipoVehiculo || sinTarifa}
                onChange={onCambio}
                className="mt-1"
            />
            <span className="flex-1">
                <span className="block font-medium">{servicio.nombre}</span>
                <span className="block text-gray-600">{servicio.descripcion}</span>
            </span>
            <span className="text-right">
                {tarifa ? (
                    <>
                        <span className="block font-medium">{formatearPrecio(tarifa.precio)}</span>
                        <span className="block text-gray-600">
                            {formatearDuracion(tarifa.duracion_min)}
                        </span>
                    </>
                ) : sinTarifa ? (
                    <span className="text-gray-600">
                        No disponible para {TIPOS_VEHICULO[tipoVehiculo].toLowerCase()}
                    </span>
                ) : null}
            </span>
        </label>
    );
}