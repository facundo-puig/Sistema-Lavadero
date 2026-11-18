"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { apiFetch } from "@/lib/api";
import { guardarSesion } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    const aviso = sessionStorage.getItem("lavadero_aviso");

    if (aviso === "sesion_expirada") {
      sessionStorage.removeItem("lavadero_aviso");

      toast.warning(
        "Tu sesión venció. Iniciá sesión nuevamente."
      );
    }
  }, []);

  async function iniciarSesion(evento) {
    evento.preventDefault();
    setError("");
    setCargando(true);

    try {
      const datos = await apiFetch("/api/auth/login/", {
        method: "POST",
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          password,
        }),
      });

      guardarSesion(datos);

      // Limpiar los campos después de iniciar sesión.
      setEmail("");
      setPassword("");

      // Redirección provisional según el rol.
      if (datos.usuario.rol === "CLIENTE") {
        router.replace("/turnos");
      } else {
        router.replace("/");
      }
    } catch (err) {
      setError(err.message || "No se pudo iniciar sesión.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-100 px-4">
      <section className="w-full max-w-md rounded-xl bg-white p-8 shadow-md">
        <h1 className="mb-2 text-center text-2xl font-bold text-gray-900">
          Sistema Lavadero
        </h1>

        <p className="mb-6 text-center text-gray-600">
          Iniciar sesión
        </p>

        <form
          onSubmit={iniciarSesion}
          autoComplete="off"
          className="space-y-4"
        >
          <div>
            <label
              htmlFor="email"
              className="mb-1 block text-sm font-medium text-gray-800"
            >
              Correo electrónico
            </label>

            <input
              id="email"
              type="email"
              autoComplete="off"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-300 p-3 text-gray-900"
              placeholder="correo@ejemplo.com"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-1 block text-sm font-medium text-gray-800"
            >
              Contraseña
            </label>

            <input
              id="password"
              type="password"
              autoComplete="off"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 p-3 text-gray-900"
              placeholder="Ingresá tu contraseña"
            />
          </div>

          {error && (
            <p role="alert" className="text-sm text-red-600">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={cargando}
            className="w-full rounded-lg bg-blue-600 p-3 font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {cargando ? "Ingresando..." : "Iniciar sesión"}
          </button>
        </form>
      </section>
    </main>
  );
}