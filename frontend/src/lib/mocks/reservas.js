// "POST /api/turnos/" simulado. Devuelve un objeto con la forma del contrato (docs/api-turnos.md).
// Cuando exista el endpoint real, esta función se reemplaza por:
//   apiFetch("/turnos/", { method: "POST", body: JSON.stringify({ vehiculo, servicios, inicio }) })
// (y se agrega el header Authorization cuando esté el login).

import { ApiError } from "@/lib/api";
import { vehiculosMock, serviciosMock } from "@/lib/mocks/datos";
import { calcularResumen } from "@/lib/turnos";

let siguienteId = 1;

const esperar = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Cuerpo igual al contrato: { vehiculo: id, servicios: [ids], inicio: ISO en UTC }.
export async function reservarTurnoMock({ vehiculo, servicios, inicio }) {
    await esperar(700);

    const veh = vehiculosMock.find((v) => v.id === vehiculo);
    const servs = serviciosMock.filter((s) => servicios.includes(s.id));
    const { precioTotal, duracionMin } = calcularResumen(servs, veh.tipo);
    const fin = new Date(new Date(inicio).getTime() + duracionMin * 60 * 1000);

    // Para probar el error 409 del contrato: la patente de la camioneta nunca tiene box libre.
    if (veh.patente === "AF456GH") {
        throw new ApiError(409, "No hay ningún box libre en ese horario.");
    }

    return {
        id: siguienteId++,
        vehiculo: { id: veh.id, patente: veh.patente, tipo: veh.tipo },
        box: { id: 1, nombre: "Box 1" },
        inicio,
        fin: fin.toISOString(),
        estado: "pendiente",
        precio_total: precioTotal,
        servicios: servs.map((s) => ({
            id: s.id,
            nombre: s.nombre,
            precio_aplicado: s.tarifas[veh.tipo].precio,
        })),
    };
}