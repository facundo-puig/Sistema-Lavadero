"use client";

import RutaProtegida from "@/components/RutaProtegida";

const ROLES_PERMITIDOS = ["CLIENTE"];

export default function VehiculosLayout({ children }) {
  return (
    <RutaProtegida rolesPermitidos={ROLES_PERMITIDOS}>
      {children}
    </RutaProtegida>
  );
}
