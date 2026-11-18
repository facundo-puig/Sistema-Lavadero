
"use client";

import { useMemo } from "react";

import RutaProtegida from "@/components/RutaProtegida";

export default function TurnosLayout({ children }) {
  const rolesPermitidos = useMemo(() => ["CLIENTE"], []);

  return (
    <RutaProtegida rolesPermitidos={rolesPermitidos}>
      {children}
    </RutaProtegida>
  );
}
