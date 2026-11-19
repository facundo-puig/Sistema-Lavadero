// Lógica de la reserva de turnos en el frontend.

import { HORARIO_ATENCION } from "@/lib/constantes";

// Argentina está en UTC-3 todo el año (sin horario de verano).
const OFFSET_ARGENTINA = "-03:00";

function aMinutos(hhmm) {
    const [h, m] = hhmm.split(":").map(Number);
    return h * 60 + m;
}

function aHHMM(minutos) {
    const h = String(Math.floor(minutos / 60)).padStart(2, "0");
    const m = String(minutos % 60).padStart(2, "0");
    return `${h}:${m}`;
}

// Tarifa de un servicio para un tipo de vehículo, o undefined si no existe.
// La API devuelve las tarifas como lista: [{ tipo_vehiculo, precio, duracion_minutos }].
export function tarifaDe(servicio, tipoVehiculo) {
    return servicio.tarifas.find((t) => t.tipo_vehiculo === tipoVehiculo);
}

// Precio total (en centavos, para no arrastrar errores de decimales) y duración total.
export function calcularResumen(servicios, tipoVehiculo) {
    let centavos = 0;
    let minutos = 0;
    for (const servicio of servicios) {
        const tarifa = tarifaDe(servicio, tipoVehiculo);
        if (!tarifa) continue;
        centavos += Math.round(parseFloat(tarifa.precio) * 100);
        minutos += tarifa.duracion_minutos;
    }
    return { precioTotal: (centavos / 100).toFixed(2), duracionMin: minutos };
}

// Horarios de inicio disponibles: cada 30 minutos dentro del horario de atención.
export function horariosDeInicio() {
    const lista = [];
    const hasta = aMinutos(HORARIO_ATENCION.hasta);
    for (let min = aMinutos(HORARIO_ATENCION.desde); min < hasta; min += 30) {
        lista.push(aHHMM(min));
    }
    return lista;
}

// Convierte fecha y hora de Argentina ("2026-11-20", "10:00") a ISO en UTC,
// que es lo que viaja en la API.
export function aIsoUtc(fecha, hora) {
    return new Date(`${fecha}T${hora}:00${OFFSET_ARGENTINA}`).toISOString();
}

// Hora de fin (HH:MM, hora de Argentina) a partir de la hora de inicio y la duración.
export function horaDeFin(hora, duracionMin) {
    return aHHMM(aMinutos(hora) + duracionMin);
}

// Valida el formulario. Devuelve un objeto { campo: "mensaje" } (vacío si todo está bien).
// El backend vuelve a validar todo, esto es solo para dar feedback rápido.
export function validarReserva({ vehiculo, servicios, fecha, hora }, ahora = Date.now()) {
    const errores = {};

    if (!vehiculo) errores.vehiculo = "Elegí un vehículo.";
    if (servicios.length === 0) errores.servicios = "Elegí al menos un servicio.";
    if (!fecha) errores.fecha = "Elegí una fecha.";
    if (!hora) errores.hora = "Elegí un horario de inicio.";

    if (fecha && hora) {
        if (new Date(aIsoUtc(fecha, hora)).getTime() <= ahora) {
            errores.fecha = "El turno tiene que ser en el futuro.";
        }
    }

    if (vehiculo && servicios.length > 0 && hora) {
        const { duracionMin } = calcularResumen(servicios, vehiculo.tipo);
        if (aMinutos(hora) + duracionMin > aMinutos(HORARIO_ATENCION.hasta)) {
            errores.hora = `El turno terminaría a las ${horaDeFin(hora, duracionMin)}, después del cierre (${HORARIO_ATENCION.hasta}). Elegí un horario más temprano.`;
        }
    }

    return errores;
}