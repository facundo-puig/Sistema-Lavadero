"use client";

// Botones Anterior y Siguiente de los listados paginados (de a 20).

const ESTILO =
    "rounded-md border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-40";

export default function Paginacion({
    pagina,
    hayAnterior,
    haySiguiente,
    deshabilitado = false,
    onAnterior,
    onSiguiente,
}) {
    return (
        <div className="mt-5 flex items-center justify-between">
            <button
                type="button"
                disabled={!hayAnterior || deshabilitado}
                onClick={onAnterior}
                className={ESTILO}
            >
                Anterior
            </button>

            <span className="text-sm text-gray-600">Página {pagina}</span>

            <button
                type="button"
                disabled={!haySiguiente || deshabilitado}
                onClick={onSiguiente}
                className={ESTILO}
            >
                Siguiente
            </button>
        </div>
    );
}
