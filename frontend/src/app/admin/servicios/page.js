"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import Boton from "@/components/Boton";
import { Campo, MensajeError, propsDeControl } from "@/components/Campo";
import Paginacion from "@/components/Paginacion";
import { apiFetch } from "@/lib/api";
import { TIPOS_VEHICULO } from "@/lib/constantes";
import { textoDeError } from "@/lib/errores";
import { formatearDuracion, formatearPrecio } from "@/lib/formatos";

const URL_SERVICIOS = "/api/servicios/";
const TIPOS = Object.keys(TIPOS_VEHICULO);
const SIN_ERRORES = { tarifas: {} };

function formularioVacio() {
  return {
    nombre: "",
    descripcion: "",
    tarifas: Object.fromEntries(
      TIPOS.map((tipo) => [tipo, { precio: "", duracion_minutos: "" }])
    ),
  };
}

function formularioDe(servicio) {
  const formulario = formularioVacio();

  formulario.nombre = servicio.nombre;
  formulario.descripcion = servicio.descripcion;

  for (const tarifa of servicio.tarifas) {
    formulario.tarifas[tarifa.tipo_vehiculo] = {
      precio: tarifa.precio,
      duracion_minutos: String(tarifa.duracion_minutos),
    };
  }

  return formulario;
}

// Validación para la experiencia de usuario: el backend valida igual.
function validarFormulario(formulario, tiposConTarifa) {
  const errores = { tarifas: {} };

  if (!formulario.nombre.trim()) {
    errores.nombre = "Ingresá el nombre del servicio.";
  }

  for (const tipo of TIPOS) {
    const { precio, duracion_minutos: duracion } = formulario.tarifas[tipo];
    const hayPrecio = precio.trim() !== "";
    const hayDuracion = duracion.trim() !== "";
    const errorTipo = {};

    if (!hayPrecio && !hayDuracion) {
      // El backend no elimina tarifas: una tarifa existente no se puede dejar vacía.
      if (tiposConTarifa.includes(tipo)) {
        errorTipo.precio =
          "Una tarifa existente no se puede quitar. Cambiá el valor o dá de baja el servicio.";
      }
    } else {
      if (!hayPrecio) {
        errorTipo.precio = "Ingresá el precio.";
      } else if (!(Number(precio) > 0)) {
        errorTipo.precio = "El precio tiene que ser mayor a 0.";
      }

      if (!hayDuracion) {
        errorTipo.duracion_minutos = "Ingresá la duración en minutos.";
      } else if (
        !Number.isInteger(Number(duracion)) ||
        Number(duracion) < 1
      ) {
        errorTipo.duracion_minutos =
          "La duración tiene que ser un número entero mayor a 0.";
      }
    }

    if (Object.keys(errorTipo).length > 0) {
      errores.tarifas[tipo] = errorTipo;
    }
  }

  return errores;
}

function hayErrores(errores) {
  return Boolean(errores.nombre) || Object.keys(errores.tarifas).length > 0;
}

// Solo se envían los tipos de vehículo que tienen precio y duración cargados.
function tarifasAEnviar(formulario) {
  return TIPOS.filter((tipo) => formulario.tarifas[tipo].precio.trim() !== "")
    .map((tipo) => ({
      tipo_vehiculo: tipo,
      precio: formulario.tarifas[tipo].precio.trim(),
      duracion_minutos: Number(formulario.tarifas[tipo].duracion_minutos),
    }));
}

// Convierte el 400 del backend. Los errores de "tarifas" vienen por posición
// (los de la lista que se envió), así que se vuelven a asociar con su tipo de vehículo.
function erroresDeServicio(error, tiposEnviados) {
  const errores = { tarifas: {} };
  const datos = error.data;

  if (!datos || typeof datos !== "object" || Array.isArray(datos)) {
    errores.general = error.message;
    return errores;
  }

  for (const [campo, valor] of Object.entries(datos)) {
    if (campo !== "tarifas") {
      errores[campo === "detail" ? "general" : campo] = textoDeError(valor);
      continue;
    }

    (Array.isArray(valor) ? valor : [valor]).forEach((item, indice) => {
      if (item && typeof item === "object") {
        errores.tarifas[tiposEnviados[indice]] = Object.fromEntries(
          Object.entries(item).map(([nombre, mensaje]) => [
            nombre,
            textoDeError(mensaje),
          ])
        );
      } else if (item) {
        errores.general = String(item);
      }
    });
  }

  return errores;
}

export default function AdministracionServiciosPage() {
  const [servicios, setServicios] = useState([]);
  const [total, setTotal] = useState(0);
  const [haySiguiente, setHaySiguiente] = useState(false);
  const [hayAnterior, setHayAnterior] = useState(false);

  const [filtroActivo, setFiltroActivo] = useState("");
  const [pagina, setPagina] = useState(1);
  const [actualizacion, setActualizacion] = useState(0);

  const [cargando, setCargando] = useState(true);
  const [errorListado, setErrorListado] = useState("");

  const [formulario, setFormulario] = useState(formularioVacio);
  const [editandoId, setEditandoId] = useState(null);
  const [tiposConTarifa, setTiposConTarifa] = useState([]);
  const [errores, setErrores] = useState(SIN_ERRORES);
  const [guardando, setGuardando] = useState(false);
  const [procesandoId, setProcesandoId] = useState(null);

  useEffect(() => {
    let vigente = true;

    async function cargarServicios() {
      try {
        const parametros = new URLSearchParams({ page: String(pagina) });

        if (filtroActivo) {
          parametros.set("activo", filtroActivo);
        }

        const datos = await apiFetch(
          `${URL_SERVICIOS}?${parametros.toString()}`
        );

        if (!vigente) return;

        setServicios(datos.results);
        setTotal(datos.count);
        setHaySiguiente(Boolean(datos.next));
        setHayAnterior(Boolean(datos.previous));
        setErrorListado("");
      } catch (error) {
        if (!vigente) return;

        setErrorListado(error.message);
        setServicios([]);
      } finally {
        if (vigente) {
          setCargando(false);
        }
      }
    }

    cargarServicios();

    return () => {
      vigente = false;
    };
  }, [pagina, filtroActivo, actualizacion]);

  function recargarListado() {
    setCargando(true);
    setActualizacion((valor) => valor + 1);
  }

  function cambiarCampo(campo, valor) {
    setFormulario((actual) => ({ ...actual, [campo]: valor }));
    setErrores((actual) => ({ ...actual, [campo]: undefined }));
  }

  function cambiarTarifa(tipo, campo, valor) {
    setFormulario((actual) => ({
      ...actual,
      tarifas: {
        ...actual.tarifas,
        [tipo]: { ...actual.tarifas[tipo], [campo]: valor },
      },
    }));
    setErrores((actual) => ({
      ...actual,
      tarifas: { ...actual.tarifas, [tipo]: undefined },
    }));
  }

  function empezarEdicion(servicio) {
    setEditandoId(servicio.id);
    setFormulario(formularioDe(servicio));
    setTiposConTarifa(servicio.tarifas.map((t) => t.tipo_vehiculo));
    setErrores(SIN_ERRORES);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function cancelarEdicion() {
    setEditandoId(null);
    setFormulario(formularioVacio());
    setTiposConTarifa([]);
    setErrores(SIN_ERRORES);
  }

  async function guardar(evento) {
    evento.preventDefault();

    const invalidos = validarFormulario(formulario, tiposConTarifa);
    setErrores(invalidos);

    if (hayErrores(invalidos)) return;

    const tarifas = tarifasAEnviar(formulario);
    const tiposEnviados = tarifas.map((t) => t.tipo_vehiculo);

    setGuardando(true);

    try {
      await apiFetch(
        editandoId ? `${URL_SERVICIOS}${editandoId}/` : URL_SERVICIOS,
        {
          method: editandoId ? "PATCH" : "POST",
          body: JSON.stringify({
            nombre: formulario.nombre.trim(),
            descripcion: formulario.descripcion.trim(),
            tarifas,
          }),
        }
      );

      toast.success(
        editandoId ? "Servicio actualizado." : "Servicio creado."
      );

      cancelarEdicion();
      recargarListado();
    } catch (error) {
      setErrores(erroresDeServicio(error, tiposEnviados));
    } finally {
      setGuardando(false);
    }
  }

  async function cambiarEstado(servicio, activo) {
    if (!activo) {
      const confirmado = window.confirm(
        `¿Querés dar de baja el servicio ${servicio.nombre}? Deja de ofrecerse en las nuevas reservas y los turnos existentes se conservan.`
      );

      if (!confirmado) return;
    }

    setProcesandoId(servicio.id);

    try {
      if (activo) {
        await apiFetch(`${URL_SERVICIOS}${servicio.id}/`, {
          method: "PATCH",
          body: JSON.stringify({ activo: true }),
        });

        toast.success("Servicio reactivado.");
      } else {
        await apiFetch(`${URL_SERVICIOS}${servicio.id}/`, {
          method: "DELETE",
        });

        toast.success("Servicio dado de baja.");

        if (editandoId === servicio.id) {
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
        <h1 className="text-2xl font-semibold">
          Administración de servicios
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          Cada servicio tiene un precio y una duración por tipo de vehículo.
        </p>
      </div>

      <form
        onSubmit={guardar}
        noValidate
        className="space-y-5 rounded-md border border-gray-200 bg-white p-5"
      >
        <h2 className="font-semibold">
          {editandoId ? "Editar servicio" : "Agregar servicio"}
        </h2>

        <div className="grid gap-4 sm:grid-cols-2">
          <Campo id="nombre" etiqueta="Nombre" error={errores.nombre}>
            <input
              {...propsDeControl("nombre", errores.nombre)}
              type="text"
              maxLength={100}
              autoComplete="off"
              placeholder="Lavado completo"
              value={formulario.nombre}
              onChange={(e) => cambiarCampo("nombre", e.target.value)}
            />
          </Campo>

          <Campo
            id="descripcion"
            etiqueta="Descripción (opcional)"
            error={errores.descripcion}
          >
            <input
              {...propsDeControl("descripcion", errores.descripcion)}
              type="text"
              autoComplete="off"
              placeholder="Exterior, interior y aspirado."
              value={formulario.descripcion}
              onChange={(e) => cambiarCampo("descripcion", e.target.value)}
            />
          </Campo>
        </div>

        <fieldset className="space-y-3">
          <legend className="text-sm font-medium">
            Tarifas por tipo de vehículo
          </legend>
          <p className="text-sm text-gray-600">
            Completá precio y duración de los tipos de vehículo que atiende
            este servicio. Los que dejes vacíos no se ofrecen. Una tarifa ya
            cargada se puede cambiar, pero no quitar.
          </p>

          {TIPOS.map((tipo) => {
            const errorTipo = errores.tarifas?.[tipo];

            return (
              <div
                key={tipo}
                className="grid gap-3 rounded-md border border-gray-200 p-3 sm:grid-cols-3"
              >
                <p className="text-sm font-medium sm:pt-2">
                  {TIPOS_VEHICULO[tipo]}
                </p>

                <Campo
                  id={`precio-${tipo}`}
                  etiqueta="Precio ($)"
                  error={errorTipo?.precio}
                >
                  <input
                    {...propsDeControl(`precio-${tipo}`, errorTipo?.precio)}
                    type="number"
                    inputMode="decimal"
                    min="0"
                    step="0.01"
                    placeholder="12500"
                    value={formulario.tarifas[tipo].precio}
                    onChange={(e) =>
                      cambiarTarifa(tipo, "precio", e.target.value)
                    }
                  />
                </Campo>

                <Campo
                  id={`duracion-${tipo}`}
                  etiqueta="Duración (min)"
                  error={errorTipo?.duracion_minutos}
                >
                  <input
                    {...propsDeControl(
                      `duracion-${tipo}`,
                      errorTipo?.duracion_minutos
                    )}
                    type="number"
                    inputMode="numeric"
                    min="1"
                    step="1"
                    placeholder="45"
                    value={formulario.tarifas[tipo].duracion_minutos}
                    onChange={(e) =>
                      cambiarTarifa(tipo, "duracion_minutos", e.target.value)
                    }
                  />
                </Campo>
              </div>
            );
          })}
        </fieldset>

        <MensajeError id="servicio-error-general" mensaje={errores.general} />

        <div className="flex flex-wrap gap-3">
          <Boton type="submit" cargando={guardando} textoCargando="Guardando...">
            {editandoId ? "Guardar cambios" : "Agregar servicio"}
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
            <h2 className="font-semibold">Servicios</h2>
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

        <MensajeError id="servicios-error-listado" mensaje={errorListado} />

        {cargando ? (
          <p className="text-sm text-gray-600">Cargando servicios...</p>
        ) : (
          <>
            {servicios.length === 0 && !errorListado && (
              <p
                role="status"
                className="rounded-md border border-dashed border-gray-300 p-4 text-sm text-gray-600"
              >
                No se encontraron servicios.
              </p>
            )}

            <ul className="space-y-2">
              {servicios.map((servicio) => (
                <li
                  key={servicio.id}
                  className="space-y-3 rounded-md border border-gray-200 bg-white p-4"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-3">
                        <p className="font-semibold">{servicio.nombre}</p>
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                            servicio.activo
                              ? "bg-green-100 text-green-800"
                              : "bg-gray-200 text-gray-700"
                          }`}
                        >
                          {servicio.activo ? "Activo" : "Inactivo"}
                        </span>
                      </div>

                      {servicio.descripcion && (
                        <p className="mt-1 text-sm text-gray-600">
                          {servicio.descripcion}
                        </p>
                      )}
                    </div>

                    <div className="flex gap-2">
                      <button
                        type="button"
                        disabled={procesandoId === servicio.id}
                        onClick={() => empezarEdicion(servicio)}
                        className="rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-100 disabled:opacity-50"
                      >
                        Editar
                      </button>

                      {servicio.activo ? (
                        <button
                          type="button"
                          disabled={procesandoId === servicio.id}
                          onClick={() => cambiarEstado(servicio, false)}
                          className="rounded-md border border-red-300 px-3 py-2 text-sm text-red-700 hover:bg-red-50 disabled:opacity-50"
                        >
                          Dar de baja
                        </button>
                      ) : (
                        <button
                          type="button"
                          disabled={procesandoId === servicio.id}
                          onClick={() => cambiarEstado(servicio, true)}
                          className="rounded-md border border-green-300 px-3 py-2 text-sm text-green-800 hover:bg-green-50 disabled:opacity-50"
                        >
                          Reactivar
                        </button>
                      )}
                    </div>
                  </div>

                  {servicio.tarifas.length === 0 ? (
                    <p className="text-sm text-amber-800">
                      Sin tarifas cargadas: no se puede reservar.
                    </p>
                  ) : (
                    <ul className="grid gap-1 text-sm text-gray-700 sm:grid-cols-3">
                      {servicio.tarifas.map((tarifa) => (
                        <li key={tarifa.id}>
                          <span className="font-medium">
                            {TIPOS_VEHICULO[tarifa.tipo_vehiculo]}:
                          </span>{" "}
                          {formatearPrecio(tarifa.precio)} ·{" "}
                          {formatearDuracion(tarifa.duracion_minutos)}
                        </li>
                      ))}
                    </ul>
                  )}
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
