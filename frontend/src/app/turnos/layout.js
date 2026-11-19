
"use client";

import RutaProtegida from "@/components/RutaProtegida";

const ROLES_PERMITIDOS = ["CLIENTE"];

export default function TurnosLayout({ children }) {
  return (
    <RutaProtegida rolesPermitidos={ROLES_PERMITIDOS}>
      {children}
    </RutaProtegida>
  );
}