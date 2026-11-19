
"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import Boton from "@/components/Boton";
import { Campo, propsDeControl } from "@/components/Campo";
import { apiFetch } from "@/lib/api";

export default function RegistroPage() {
  const router = useRouter();

  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmarPassword, setConfirmarPassword] = useState("");
  const [errores, setErrores] = useState({});
  const [cargando, setCargando] = useState(false);

  async function registrarCliente(evento) {
    evento.preventDefault();
    setErrores({});

    if (password !== confirmarPassword) {
      setErrores({
        confirmarPassword: "Las contraseñas no coinciden.",
      });
      setPassword("");
      setConfirmarPassword("");
      toast.error("Las contraseñas no coinciden.");
      return;
    }

    setCargando(true);

    try {
      await apiFetch("/api/auth/registro/", {
        method: "POST",
        body: JSON.stringify({
          nombre: nombre.trim(),
          email: email.trim().toLowerCase(),
          password,
        }),
      });

      // Limpiamos los campos después del registro exitoso.
      setNombre("");
      setEmail("");
      setPassword("");
      setConfirmarPassword("");

      toast.success(
        "Cuenta creada correctamente. Ya podés iniciar sesión."
      );

      router.push("/login");
    } catch (error) {
      // Conservamos nombre y email, pero borramos las contraseñas.
      setPassword("");
      setConfirmarPassword("");

      const datos = error.data;

      if (datos && typeof datos === "object") {
        const erroresBackend = {};

        for (const [campo, mensajes] of Object.entries(datos)) {
          erroresBackend[campo] = Array.isArray(mensajes)
            ? mensajes.join(" ")
            : String(mensajes);
        }

        setErrores(erroresBackend);

        const primerError = Object.values(erroresBackend)[0];

        toast.error(
          primerError || "No se pudo completar el registro."
        );
      } else {
        toast.error(
          error.message || "No se pudo completar el registro."
        );
      }
    } finally {
      setCargando(false);
    }
  }

  return (
    <section className="mx-auto w-full max-w-md rounded-xl bg-white p-8 shadow-md">
      <h1 className="mb-2 text-center text-2xl font-bold text-gray-900">
        Sistema Lavadero
      </h1>

      <p className="mb-6 text-center text-gray-600">
        Crear cuenta de cliente
      </p>

      <form onSubmit={registrarCliente} className="space-y-4">
        <Campo id="nombre" etiqueta="Nombre" error={errores.nombre}>
          <input
            {...propsDeControl("nombre", errores.nombre)}
            type="text"
            autoComplete="given-name"
            required
            maxLength={150}
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Ingresá tu nombre"
          />
        </Campo>

        <Campo
          id="email"
          etiqueta="Correo electrónico"
          error={errores.email}
        >
          <input
            {...propsDeControl("email", errores.email)}
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="correo@ejemplo.com"
          />
        </Campo>

        <Campo
          id="password"
          etiqueta="Contraseña"
          error={errores.password}
        >
          <input
            {...propsDeControl("password", errores.password)}
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Mínimo 8 caracteres"
          />
        </Campo>

        <Campo
          id="confirmarPassword"
          etiqueta="Confirmar contraseña"
          error={errores.confirmarPassword}
        >
          <input
            {...propsDeControl(
              "confirmarPassword",
              errores.confirmarPassword
            )}
            type="password"
            autoComplete="new-password"
            required
            value={confirmarPassword}
            onChange={(e) => setConfirmarPassword(e.target.value)}
            placeholder="Repetí tu contraseña"
          />
        </Campo>

        <Boton
          type="submit"
          cargando={cargando}
          textoCargando="Registrando..."
          className="w-full"
        >
          Crear cuenta
        </Boton>
      </form>

      <p className="mt-6 text-center text-sm text-gray-600">
        ¿Ya tenés una cuenta?{" "}
        <Link
          href="/login"
          className="font-medium text-blue-600 hover:underline"
        >
          Iniciar sesión
        </Link>
      </p>
    </section>
  );
}
