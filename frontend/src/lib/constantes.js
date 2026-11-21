export const TIPOS_VEHICULO = {
    auto: "Auto",
    camioneta: "Camioneta",
    moto: "Moto",
};

export const ESTADOS_TURNO = {
    pendiente: "Pendiente",
    en_proceso: "En proceso",
    finalizado: "Finalizado",
    entregado: "Entregado",
    cancelado: "Cancelado",
};

// Horario de atención (hora de Argentina).
export const HORARIO_ATENCION = { desde: "08:00", hasta: "20:00" };

export const ZONA_HORARIA = "America/Argentina/Buenos_Aires";

// Flujo de estados de un turno: cada estado solo avanza al siguiente (el backend lo valida igual).
export const SIGUIENTE_ESTADO = {
    pendiente: "en_proceso",
    en_proceso: "finalizado",
    finalizado: "entregado",
};

// Texto del botón que avanza el turno al siguiente estado.
export const ACCION_AVANZAR = {
    pendiente: "Iniciar",
    en_proceso: "Finalizar",
    finalizado: "Entregar",
};