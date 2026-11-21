
"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import Boton from "@/components/Boton";
import { apiFetch } from "@/lib/api";
import { obtenerSesion } from "@/lib/auth";

const URL_USUARIOS = "/api/auth/usuarios/";

const ROLES = ["CLIENTE", "OPERARIO", "ADMINISTRADOR"];

function obtenerMensajeError(error) {
  const datos = error.data;

  if (datos && typeof datos === "object") {
    const primerCampo = Object.values(datos)[0];

    if (Array.isArray(primerCampo)) {
      return primerCampo.join(" ");
    }

    if (primerCampo) {
      return String(primerCampo);
    }
  }

  return error.message || "Ocurrió un error.";
}

export default function AdministracionUsuariosPage() {
  const [usuarios, setUsuarios] = useState([]);
  const [total, setTotal] = useState(0);
  const [siguiente, setSiguiente] = useState(false);
  const [anterior, setAnterior] = useState(false);

  const [filtroRol, setFiltroRol] = useState("");
  const [pagina, setPagina] = useState(1);
  const [actualizacion, setActualizacion] = useState(0);

  const [cargando, setCargando] = useState(true);
  const [procesando, setProcesando] = useState(false);
  const [procesandoId, setProcesandoId] = useState(null);
  const [errorListado, setErrorListado] = useState("");

  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rolNuevo, setRolNuevo] = useState("OPERARIO");

  const administradorId = obtenerSesion()?.usuario?.id;

  useEffect(() => {
    let vigente = true;

    async function cargarUsuarios() {
      try {
        const parametros = new URLSearchParams({
          page: String(pagina),
        });

        if (filtroRol) {
          parametros.set("rol", filtroRol);
        }

        const datos = await apiFetch(
          `${URL_USUARIOS}?${parametros.toString()}`
        );

        if (!vigente) return;

        setUsuarios(datos.results);
        setTotal(datos.count);
        setSiguiente(Boolean(datos.next));
        setAnterior(Boolean(datos.previous));
        setErrorListado("");
      } catch (error) {
        if (!vigente) return;

        setErrorListado(obtenerMensajeError(error));
        setUsuarios([]);
      } finally {
        if (vigente) {
          setCargando(false);
        }
      }
    }

    cargarUsuarios();

    return () => {
      vigente = false;
    };
  }, [pagina, filtroRol, actualizacion]);

  function recargarListado() {
    setCargando(true);
    setActualizacion((valor) => valor + 1);
  }

  async function crearUsuario(evento) {
    evento.preventDefault();
    setProcesando(true);

    try {
      await apiFetch(URL_USUARIOS, {
        method: "POST",
        body: JSON.stringify({
          nombre: nombre.trim(),
          email: email.trim().toLowerCase(),
          password,
          rol: rolNuevo,
        }),
      });

      toast.success("Usuario creado correctamente.");

      setNombre("");
      setEmail("");
      setPassword("");
      setRolNuevo("OPERARIO");

      setPagina(1);
      recargarListado();
    } catch (error) {
      toast.error(obtenerMensajeError(error));
      setPassword("");
    } finally {
      setProcesando(false);
    }
  }

  async function cambiarRol(usuario, nuevoRol) {
    if (usuario.rol === nuevoRol) return;

    setProcesandoId(usuario.id);

    try {
      await apiFetch(
        `${URL_USUARIOS}${usuario.id}/rol/`,
        {
          method: "PATCH",
          body: JSON.stringify({ rol: nuevoRol }),
        }
      );

      toast.success("Rol actualizado correctamente.");
      recargarListado();
    } catch (error) {
      toast.error(obtenerMensajeError(error));
    } finally {
      setProcesandoId(null);
    }
  }

  async function darDeBaja(usuario) {
    const confirmado = window.confirm(
      `¿Querés dar de baja a ${usuario.email}?`
    );

    if (!confirmado) return;

    setProcesandoId(usuario.id);

    try {
      await apiFetch(`${URL_USUARIOS}${usuario.id}/`, {
        method: "DELETE",
      });

      toast.success("Usuario dado de baja correctamente.");
      recargarListado();
    } catch (error) {
      toast.error(obtenerMensajeError(error));
    } finally {
      setProcesandoId(null);
    }
  }

  return (
    <main className="mx-auto max-w-6xl space-y-8 px-4 py-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Administración de usuarios
        </h1>
        <p className="mt-1 text-gray-600">
          Gestioná las cuentas y los permisos del lavadero.
        </p>
      </div>

      <section className="rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="mb-5 text-xl font-semibold text-gray-900">
          Crear operario o administrador
        </h2>

        <form
          onSubmit={crearUsuario}
          className="grid gap-4 md:grid-cols-2"
        >
          <div>
            <label
              htmlFor="nombre"
              className="mb-1 block text-sm font-medium"
            >
              Nombre
            </label>
            <input
              id="nombre"
              type="text"
              required
              maxLength={150}
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              className="w-full rounded-lg border border-gray-300 p-3"
            />
          </div>

          <div>
            <label
              htmlFor="email"
              className="mb-1 block text-sm font-medium"
            >
              Correo electrónico
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-300 p-3"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-1 block text-sm font-medium"
            >
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 p-3"
            />
          </div>

          <div>
            <label
              htmlFor="rolNuevo"
              className="mb-1 block text-sm font-medium"
            >
              Rol
            </label>
            <select
              id="rolNuevo"
              value={rolNuevo}
              onChange={(e) => setRolNuevo(e.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white p-3"
            >
              <option value="OPERARIO">Operario</option>
              <option value="ADMINISTRADOR">Administrador</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <Boton
              type="submit"
              cargando={procesando}
              textoCargando="Creando..."
            >
              Crear usuario
            </Boton>
          </div>
        </form>
      </section>

      <section className="rounded-xl border border-gray-200 bg-white p-6">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Usuarios registrados
            </h2>
            <p className="text-sm text-gray-600">
              Total: {total}
            </p>
          </div>

          <div>
            <label
              htmlFor="filtroRol"
              className="mb-1 block text-sm font-medium"
            >
              Filtrar por rol
            </label>
            <select
              id="filtroRol"
              value={filtroRol}
              onChange={(e) => {
                setFiltroRol(e.target.value);
                setPagina(1);
                setCargando(true);
              }}
              className="rounded-lg border border-gray-300 bg-white p-2"
            >
              <option value="">Todos</option>
              {ROLES.map((rol) => (
                <option key={rol} value={rol}>
                  {rol}
                </option>
              ))}
            </select>
          </div>
        </div>

        {errorListado && (
          <p role="alert" className="mb-4 text-sm text-red-600">
            {errorListado}
          </p>
        )}

        {cargando ? (
          <p className="py-6 text-gray-600">
            Cargando usuarios...
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b bg-gray-50">
                <tr>
                  <th className="p-3">Nombre</th>
                  <th className="p-3">Email</th>
                  <th className="p-3">Rol</th>
                  <th className="p-3">Estado</th>
                  <th className="p-3">Acciones</th>
                </tr>
              </thead>

              <tbody>
                {usuarios.map((usuario) => {
                  const esPropio =
                    usuario.id === administradorId;

                  return (
                    <tr
                      key={usuario.id}
                      className="border-b"
                    >
                      <td className="p-3">
                        {usuario.nombre || "Sin nombre"}
                      </td>

                      <td className="p-3">{usuario.email}</td>

                      <td className="p-3">
                        <select
                          aria-label={`Rol de ${usuario.email}`}
                          value={usuario.rol}
                          disabled={
                            esPropio ||
                            !usuario.is_active ||
                            procesandoId === usuario.id
                          }
                          onChange={(e) =>
                            cambiarRol(usuario, e.target.value)
                          }
                          className="rounded border border-gray-300 bg-white p-2 disabled:opacity-50"
                        >
                          {ROLES.map((rol) => (
                            <option key={rol} value={rol}>
                              {rol}
                            </option>
                          ))}
                        </select>
                      </td>

                      <td className="p-3">
                        {usuario.is_active ? "Activo" : "Inactivo"}
                      </td>

                      <td className="p-3">
                        <button
                          type="button"
                          disabled={
                            esPropio ||
                            !usuario.is_active ||
                            procesandoId === usuario.id
                          }
                          onClick={() => darDeBaja(usuario)}
                          className="rounded border border-red-300 px-3 py-2 text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-40"
                        >
                          Dar de baja
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {usuarios.length === 0 && !errorListado && (
              <p className="py-6 text-center text-gray-600">
                No se encontraron usuarios.
              </p>
            )}
          </div>
        )}

        <div className="mt-5 flex items-center justify-between">
          <button
            type="button"
            disabled={!anterior || cargando}
            onClick={() => {
              setCargando(true);
              setPagina((valor) => Math.max(1, valor - 1));
            }}
            className="rounded-lg border px-4 py-2 disabled:opacity-40"
          >
            Anterior
          </button>

          <span className="text-sm text-gray-600">
            Página {pagina}
          </span>

          <button
            type="button"
            disabled={!siguiente || cargando}
            onClick={() => {
              setCargando(true);
              setPagina((valor) => valor + 1);
            }}
            className="rounded-lg border px-4 py-2 disabled:opacity-40"
          >
            Siguiente
          </button>
        </div>
      </section>
    </main>
  );
}
