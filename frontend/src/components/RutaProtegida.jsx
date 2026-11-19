
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { obtenerSesion } from "@/lib/auth";

export default function RutaProtegida({
  children,
  rolesPermitidos = [],
}) {
  const router = useRouter();
  const [autorizado, setAutorizado] = useState(false);

  useEffect(() => {
    const sesion = obtenerSesion();

    if (!sesion?.access || !sesion?.usuario) {
      toast.warning("Tenés que iniciar sesión para continuar.");
      router.replace("/login");
      return;
    }

    if (!rolesPermitidos.includes(sesion.usuario.rol)) {
      toast.error("No tenés permiso para acceder a esta página.");
      router.replace("/");
      return;
    }

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setAutorizado(true);
  }, [router, rolesPermitidos]);

  if (!autorizado) {
    return (
      <div className="py-10 text-center text-gray-600">
        Verificando permisos...
      </div>
    );
  }

  return children;
}
