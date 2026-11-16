// Piezas comunes de los formularios: etiqueta, mensaje de error y estilo de los controles.

const ESTILO_BASE =
    "mt-1 block w-full rounded-md border bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500";

// Props que tiene que llevar el control (id, estilo y accesibilidad) según haya error o no.
export function propsDeControl(id, error) {
    return {
        id,
        "aria-invalid": Boolean(error),
        "aria-describedby": error ? `${id}-error` : undefined,
        className: `${ESTILO_BASE} ${error ? "border-red-500" : "border-gray-300"}`,
    };
}

// Mensaje de error en rojo. No muestra nada si no hay mensaje.
export function MensajeError({ id, mensaje }) {
    if (!mensaje) return null;
    return (
        <p id={id} role="alert" className="mt-1 text-sm text-red-600">
            {mensaje}
        </p>
    );
}

export function Campo({ id, etiqueta, error, children }) {
    return (
        <div>
            <label htmlFor={id} className="block text-sm font-medium">
                {etiqueta}
            </label>
            {children}
            <MensajeError id={`${id}-error`} mensaje={error} />
        </div>
    );
}