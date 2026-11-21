"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import Boton from "@/components/Boton";
import { Campo, MensajeError, propsDeControl } from "@/components/Campo";
import Paginacion from "@/components/Paginacion";
import { apiFetch } from "@/lib/api";
import { erroresDeApi } from "@/lib/errores";

const URL_BOXES = "/api/boxes/";

export default function AdministracionBoxesPage() {
  const [boxes, setBoxes] = useState([]);
  const [total, setTotal] = useState(0);
  const [haySiguiente, setHaySiguiente] = useState(false);
  const [hayAnterior, setHayAnterior] = useState(false);

  const [filtroActivo, setFiltroActivo] = useState("");
  const [pagina, setPagina] = useState(1);
  const [actualizacion, setActualizacion] = useState(0);

  const [cargando, setCargando] = useState(true);
  const [errorListado, setErrorListado] = useState("");

  const [nombre, setNombre] = useState("");
  const [editandoId, setEditandoId] = useState(null);
  const [errores, setErrores] = useState({});
  const [guardando, setGuardando] = useState(false);
  const [procesandoId, setProcesandoId] = useState(null);

  useEffect(() => {
    let vigente = true;

    async function cargarBoxes() {
      try {
        const parametros = new URLSearchParams({ page: String(pagina) });

        if (filtroActivo) {
          parametros.set("activo", filtroActivo);
        }

        const datos = await apiFetch(`${URL_BOXES}?${parametros.toString()}`);

        if (!vigente) return;

        setBoxes(datos.results);
        setTotal(datos.count);
        setHaySiguiente(Boolean(datos.next));
        setHayAnterior(Boolean(datos.previous));
        setErrorListado("");
      } catch (error) {
        if (!vigente) return;

        setErrorListado(error.message);
        setBoxes([]);
      } finally {
        if (vigente) {
          setCargando(false);
        }
      }
    }

    cargarBoxes();

    return () => {
      vigente = false;
    };
  }, [pagina, filtroActivo, actualizacion]);

  function recargarListado() {
    setCargando(true);
    setActualizacion((valor) => valor + 1);
  }

  function empezarEdicion(box) {
    setEditandoId(box.id);
    setNombre(box.nombre);
    setErrores({});
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function cancelarEdicion() {
    setEditandoId(null);
    setNombre("");
    setErrores({});
  }

  async function guardar(evento) {
    evento.preventDefault();

    if (!nombre.trim()) {
      setErrores({ nombre: "Ingresá el nombre del box." });
      return;
    }

    setGuardando(true);

    try {
      await apiFetch(
        editandoId ? `${URL_BOXES}${editandoId}/` : URL_BOXES,
        {
          method: editandoId ? "PATCH" : "POST",
          body: JSON.stringify({ nombre: nombre.trim() }),
        }
      );

      toast.success(editandoId ? "Box actualizado." : "Box creado.");

      cancelarEdicion();
      recargarListado();
    } catch (error) {
      setErrores(erroresDeApi(error));
    } finally {
      setGuardando(false);
    }
  }

  async function cambiarEstado(box, activo) {
    if (!activo) {
      const confirmado = window.confirm(
        `¿Querés dar de baja el box ${box.nombre}? Deja de asignarse a las nuevas reservas y los turnos existentes se conservan.`
      );

      if (!confirmado) return;
    }

    setProcesandoId(box.id);

    try {
      if (activo) {
        await apiFetch(`${URL_BOXES}${box.id}/`, {
          method: "PATCH",
          body: JSON.stringify({ activo: true }),
        });

        toast.success("Box reactivado.");
      } else {
        await apiFetch(`${URL_BOXES}${box.id}/`, { method: "DELETE" });

        toast.success("Box dado de baja.");

        if (editandoId === box.id) {
          cancelarEdicion();
        }
      }

      recargarListado();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setProcesandoId(null);
    }
  }

  return (
    <section className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Administración de boxes</h1>
        <p className="mt-1 text-sm text-gray-600">
          Los boxes activos son los que se asignan a las reservas.
        </p>
      </div>

      <form
        onSubmit={guardar}
        noValidate
        className="space-y-4 rounded-md border border-gray-200 bg-white p-5"
      >
        <h2 className="font-semibold">
          {editandoId ? "Editar box" : "Agregar box"}
        </h2>

        <div className="max-w-sm">
          <Campo id="nombre" etiqueta="Nombre" error={errores.nombre}>
            <input
              {...propsDeControl("nombre", errores.nombre)}
              type="text"
              maxLength={50}
              autoComplete="off"
              placeholder="Box 3"
              value={nombre}
              onChange={(e) => {
                setNombre(e.target.value);
                setErrores({});
              }}
            />
          </Campo>
        </div>

        <MensajeError id="box-error-general" mensaje={errores.general} />

        <div className="flex flex-wrap gap-3">
          <Boton type="submit" cargando={guardando} textoCargando="Guardando...">
            {editandoId ? "Guardar cambios" : "Agregar box"}
          </Boton>

          {editandoId && (
            <button
              type="button"
              onClick={cancelarEdicion}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-100"
            >
              Cancelar
            </button>
          )}
        </div>
      </form>

      <div>
        <div className="mb-3 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="font-semibold">Boxes</h2>
            <p className="text-sm text-gray-600">Total: {total}</p>
          </div>

          <div>
            <label htmlFor="filtroActivo" className="block text-sm font-medium">
              Mostrar
            </label>
            <select
              id="filtroActivo"
              value={filtroActivo}
              onChange={(e) => {
                setFiltroActivo(e.target.value);
                setPagina(1);
                setCargando(true);
              }}
              className="mt-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
            >
              <option value="">Todos</option>
              <option value="true">Activos</option>
              <option value="false">Inactivos</option>
            </select>
          </div>
        </div>

        <MensajeError id="boxes-error-listado" mensaje={errorListado} />

        {cargando ? (
          <p className="text-sm text-gray-600">Cargando boxes...</p>
        ) : (
          <>
            {boxes.length === 0 && !errorListado && (
              <p
                role="status"
                className="rounded-md border border-dashed border-gray-300 p-4 text-sm text-gray-600"
              >
                No se encontraron boxes.
              </p>
            )}

            <ul className="space-y-2">
              {boxes.map((box) => (
                <li
                  key={box.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-gray-200 bg-white p-4"
                >
                  <div className="flex items-center gap-3">
                    <p className="font-semibold">{box.nombre}</p>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        box.activo
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-200 text-gray-700"
                      }`}
                    >
                      {box.activo ? "Activo" : "Inactivo"}
                    </span>
                  </div>

                  <div className="flex gap-2">
                    <button
                      type="button"
                      disabled={procesandoId === box.id}
                      onClick={() => empezarEdicion(box)}
                      className="rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-100 disabled:opacity-50"
                    >
                      Editar
                    </button>

                    {box.activo ? (
                      <button
                        type="button"
                        disabled={procesandoId === box.id}
                        onClick={() => cambiarEstado(box, false)}
                        className="rounded-md border border-red-300 px-3 py-2 text-sm text-red-700 hover:bg-red-50 disabled:opacity-50"
                      >
                        Dar de baja
                      </button>
                    ) : (
                      <button
                        type="button"
                        disabled={procesandoId === box.id}
                        onClick={() => cambiarEstado(box, true)}
                        className="rounded-md border border-green-300 px-3 py-2 text-sm text-green-800 hover:bg-green-50 disabled:opacity-50"
                      >
                        Reactivar
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}

        <Paginacion
          pagina={pagina}
          hayAnterior={hayAnterior}
          haySiguiente={haySiguiente}
          deshabilitado={cargando}
          onAnterior={() => {
            setCargando(true);
            setPagina((valor) => Math.max(1, valor - 1));
          }}
          onSiguiente={() => {
            setCargando(true);
            setPagina((valor) => valor + 1);
          }}
        />
      </div>
    </section>
  );
}
