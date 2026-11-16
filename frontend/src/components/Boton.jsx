"use client";

// Botón principal. Mientras 'cargando' es true queda deshabilitado y muestra 'textoCargando'.

export default function Boton({
    children,
    cargando = false,
    textoCargando,
    className = "",
    type = "button",
    ...props
}) {
    return (
        <button
            type={type}
            disabled={cargando || props.disabled}
            className={`rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 ${className}`}
            {...props}
        >
            {cargando && textoCargando ? textoCargando : children}
        </button>
    );
}