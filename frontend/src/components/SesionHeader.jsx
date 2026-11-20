"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { toast } from "sonner";

import { cerrarSesion } from "@/lib/api";
import { obtenerSesion } from "@/lib/auth";

export default function SesionHeader() {
  const router = useRouter();
  const pathname = usePathname();

  const [usuario, setUsuario] = useState(null);
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    function actualizarUsuario() {
      setUsuario(obtenerSesion()?.usuario ?? null);
    }

    // Se sincroniza con los cambios de sesión del navegador.
    window.addEventListener("lavadero:sesion", actualizarUsuario);

    return () => {
      window.removeEventListener(
        "lavadero:sesion",
        actualizarUsuario
      );
    };
  }, []);

  useEffect(() => {
    // Actualiza el encabezado al navegar entre páginas.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setUsuario(obtenerSesion()?.usuario ?? null);
  }, [pathname]);

  async function manejarLogout() {
    setCargando(true);

    try {
      await cerrarSesion();
      toast.success("Sesión cerrada correctamente.");
    } catch {
      toast.warning(
        "Se cerró la sesión local, pero no se pudo confirmar el cierre en el servidor."
      );
    } finally {
      setCargando(false);
      router.replace("/login");
    }
  }

  if (!usuario) {
    return (
      <a
        href="/login"
        className="text-sm font-medium text-blue-600"
      >
        Iniciar sesión
      </a>
    );
  }

  return (
    <div className="flex items-center gap-3">
      {usuario.rol === "CLIENTE" && (
        <nav className="flex items-center gap-3 text-sm font-medium">
          <Link
            href="/turnos"
            className="text-blue-600 hover:underline"
          >
            Mis turnos
          </Link>

          <Link
            href="/turnos/nuevo"
            className="text-blue-600 hover:underline"
          >
            Reservar
          </Link>
        </nav>
      )}

      {(usuario.rol === "ADMINISTRADOR" ||
        usuario.rol === "OPERARIO") && (
          <nav className="flex items-center gap-3 text-sm font-medium">
            <Link
              href="/agenda"
              className="text-blue-600 hover:underline"
            >
              Agenda
            </Link>
            {usuario.rol === "ADMINISTRADOR" && (
              <Link
                href="/resumen"
                className="text-blue-600 hover:underline"
              >
                Resumen
              </Link>
            )}
          </nav>
        )}

      {usuario.rol === "ADMINISTRADOR" && (
        <Link
          href="/admin/usuarios"
          className="text-sm font-medium text-blue-600 hover:underline"
        >
          Usuarios
        </Link>
      )}

      <span className="hidden text-sm text-gray-600 sm:inline">
        {usuario.email}
      </span>

      <button
        type="button"
        onClick={manejarLogout}
        disabled={cargando}
        className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium hover:bg-gray-100 disabled:opacity-50"
      >
        {cargando ? "Cerrando..." : "Cerrar sesión"}
      </button>
    </div>
  );
}