"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import Boton from "@/components/Boton";
import { Campo, MensajeError, propsDeControl } from "@/components/Campo";
import { apiFetch } from "@/lib/api";
import { TIPOS_VEHICULO } from "@/lib/constantes";

const URL_VEHICULOS = "/api/vehiculos/";
const FORMULARIO_VACIO = { patente: "", tipo: "" };

// Convierte el 400 del backend ({"campo": ["mensaje"]}) en un mensaje por campo.
function erroresDeApi(error) {
  const datos = error.data;

  if (!datos || typeof datos !== "object") {
    return { general: error.message };
  }

  const errores = {};

  for (const [campo, mensajes] of Object.entries(datos)) {
    const texto = Array.isArray(mensajes)
      ? mensajes.join(" ")
      : String(mensajes);

    errores[campo === "detail" ? "general" : campo] = texto;
  }

  return errores;
}

// El listado viene paginado de a 20: se piden todas las páginas (un cliente tiene pocos vehículos).
async function cargarVehiculos() {
  const vehiculos = [];
  let pagina = 1;
  let hayMas = true;

  while (hayMas) {
    const datos = await apiFetch(`${URL_VEHICULOS}?page=${pagina}`);

    vehiculos.push(...datos.results);
    hayMas = Boolean(datos.next);
    pagina += 1;
  }

  return vehiculos;
}

export default function VehiculosPage() {
  const [vehiculos, setVehiculos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [errorListado, setErrorListado] = useState("");
  const [actualizacion, setActualizacion] = useState(0);

  const [formulario, setFormulario] = useState(FORMULARIO_VACIO);
  const [editandoId, setEditandoId] = useState(null);
  const [errores, setErrores] = useState({});
  const [guardando, setGuardando] = useState(false);
  const [procesandoId, setProcesandoId] = useState(null);

  useEffect(() => {
    let vigente = true;

    async function cargar() {
      try {
        const lista = await cargarVehiculos();

        if (!vigente) return;

        setVehiculos(lista);
        setErrorListado("");
      } catch (error) {
        if (!vigente) return;

        setErrorListado(error.message);
      } finally {
        if (vigente) {
          setCargando(false);
        }
      }
    }

    cargar();

    return () => {
      vigente = false;
    };
  }, [actualizacion]);

  function recargarListado() {
    setCargando(true);
    setActualizacion((valor) => valor + 1);
  }

  function cambiarCampo(campo, valor) {
    setFormulario((actual) => ({ ...actual, [campo]: valor }));
    setErrores((actual) => ({ ...actual, [campo]: undefined }));
  }

  function empezarEdicion(vehiculo) {
    setEditandoId(vehiculo.id);
    setFormulario({ patente: vehiculo.patente, tipo: vehiculo.tipo });
    setErrores({});
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function cancelarEdicion() {
    setEditandoId(null);
    setFormulario(FORMULARIO_VACIO);
    setErrores({});
  }

  function validarFormulario() {
    const nuevos = {};

    if (!formulario.patente.trim()) {
      nuevos.patente = "Ingresá la patente.";
    }

    if (!formulario.tipo) {
      nuevos.tipo = "Elegí el tipo de vehículo.";
    }

    return nuevos;
  }

  async function guardar(evento) {
    evento.preventDefault();

    const invalidos = validarFormulario();
    setErrores(invalidos);

    if (Object.keys(invalidos).length > 0) return;

    setGuardando(true);

    try {
      const url = editandoId
        ? `${URL_VEHICULOS}${editandoId}/`
        : URL_VEHICULOS;

      await apiFetch(url, {
        method: editandoId ? "PATCH" : "POST",
        body: JSON.stringify({
          patente: formulario.patente.trim(),
          tipo: formulario.tipo,
        }),
      });

      toast.success(
        editandoId ? "Vehículo actualizado." : "Vehículo registrado."
      );

      cancelarEdicion();
      recargarListado();
    } catch (error) {
      setErrores(erroresDeApi(error));
    } finally {
      setGuardando(false);
    }
  }

  async function darDeBaja(vehiculo) {
    const confirmado = window.confirm(
      `¿Querés dar de baja el vehículo ${vehiculo.patente}?`
    );

    if (!confirmado) return;

    setProcesandoId(vehiculo.id);

    try {
      await apiFetch(`${URL_VEHICULOS}${vehiculo.id}/`, {
        method: "DELETE",
      });

      toast.success("Vehículo dado de baja.");

      if (editandoId === vehiculo.id) {
        cancelarEdicion();
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
        <h1 className="text-2xl font-semibold">Mis vehículos</h1>
        <p className="mt-1 text-sm text-gray-600">
          Registrá tus vehículos para poder reservar turnos.
        </p>
      </div>

      <form
        onSubmit={guardar}
        noValidate
        className="space-y-4 rounded-md border border-gray-200 bg-white p-5"
      >
        <h2 className="font-semibold">
          {editandoId ? "Editar vehículo" : "Agregar vehículo"}
        </h2>

        <div className="grid gap-4 sm:grid-cols-2">
          <Campo id="patente" etiqueta="Patente" error={errores.patente}>
            <input
              {...propsDeControl("patente", errores.patente)}
              type="text"
              maxLength={12}
              autoCapitalize="characters"
              autoComplete="off"
              placeholder="ABC123 o AB123CD"
              value={formulario.patente}
              onChange={(e) => cambiarCampo("patente", e.target.value)}
            />
          </Campo>

          <Campo id="tipo" etiqueta="Tipo de vehículo" error={errores.tipo}>
            <select
              {...propsDeControl("tipo", errores.tipo)}
              value={formulario.tipo}
              onChange={(e) => cambiarCampo("tipo", e.target.value)}
            >
              <option value="">Elegí un tipo…</option>
              {Object.entries(TIPOS_VEHICULO).map(([valor, nombre]) => (
                <option key={valor} value={valor}>
                  {nombre}
                </option>
              ))}
            </select>
          </Campo>
        </div>

        <MensajeError id="vehiculo-error-general" mensaje={errores.general} />

        <div className="flex flex-wrap gap-3">
          <Boton type="submit" cargando={guardando} textoCargando="Guardando...">
            {editandoId ? "Guardar cambios" : "Agregar vehículo"}
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
        <h2 className="mb-3 font-semibold">Vehículos registrados</h2>

        <MensajeError id="vehiculos-error-listado" mensaje={errorListado} />

        {cargando ? (
          <p className="text-sm text-gray-600">Cargando vehículos...</p>
        ) : (
          <>
            {vehiculos.length === 0 && !errorListado && (
              <p
                role="status"
                className="rounded-md border border-dashed border-gray-300 p-4 text-sm text-gray-600"
              >
                Todavía no registraste ningún vehículo.
              </p>
            )}

            <ul className="space-y-2">
              {vehiculos.map((vehiculo) => (
                <li
                  key={vehiculo.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-gray-200 bg-white p-4"
                >
                  <div>
                    <p className="font-semibold tracking-wide">
                      {vehiculo.patente}
                    </p>
                    <p className="text-sm text-gray-600">
                      {TIPOS_VEHICULO[vehiculo.tipo]}
                    </p>
                  </div>

                  <div className="flex gap-2">
                    <button
                      type="button"
                      disabled={procesandoId === vehiculo.id}
                      onClick={() => empezarEdicion(vehiculo)}
                      className="rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-100 disabled:opacity-50"
                    >
                      Editar
                    </button>

                    <button
                      type="button"
                      disabled={procesandoId === vehiculo.id}
                      onClick={() => darDeBaja(vehiculo)}
                      className="rounded-md border border-red-300 px-3 py-2 text-sm text-red-700 hover:bg-red-50 disabled:opacity-50"
                    >
                      Dar de baja
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </section>
  );
}
