// Datos de prueba para la pantalla de reserva.
// Reemplazan a la API real hasta que existan los endpoints de vehículos y servicios.
// Cuando existan, esta fuente se cambia por apiFetch() y el resto de la pantalla no se toca.

export const vehiculosMock = [
    { id: 1, patente: "AB123CD", tipo: "auto", activo: true },
    { id: 2, patente: "AF456GH", tipo: "camioneta", activo: true },
    { id: 3, patente: "512ABC", tipo: "moto", activo: true },
    { id: 4, patente: "OLD999", tipo: "auto", activo: false },
];

// Cada servicio tiene una tarifa (precio y duración en minutos) por tipo de vehículo.
// "Encerado" no tiene tarifa para moto, para probar ese caso.
export const serviciosMock = [
    {
        id: 1,
        nombre: "Lavado exterior",
        descripcion: "Lavado de carrocería y llantas.",
        activo: true,
        tarifas: {
            auto: { precio: "6000.00", duracion_min: 30 },
            camioneta: { precio: "8000.00", duracion_min: 40 },
            moto: { precio: "3500.00", duracion_min: 20 },
        },
    },
    {
        id: 2,
        nombre: "Lavado completo",
        descripcion: "Exterior, interior y aspirado.",
        activo: true,
        tarifas: {
            auto: { precio: "9000.00", duracion_min: 60 },
            camioneta: { precio: "12000.00", duracion_min: 80 },
            moto: { precio: "5000.00", duracion_min: 30 },
        },
    },
    {
        id: 3,
        nombre: "Encerado",
        descripcion: "Cera protectora sobre la carrocería.",
        activo: true,
        tarifas: {
            auto: { precio: "3500.00", duracion_min: 30 },
            camioneta: { precio: "4500.00", duracion_min: 40 },
        },
    },
    {
        id: 4,
        nombre: "Limpieza de tapizados",
        descripcion: "Limpieza profunda de asientos.",
        activo: false,
        tarifas: {
            auto: { precio: "15000.00", duracion_min: 90 },
        },
    },
];