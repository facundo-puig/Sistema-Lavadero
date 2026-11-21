"use client";

import RutaProtegida from "@/components/RutaProtegida";

const ROLES_PERMITIDOS = ["ADMINISTRADOR"];

export default function AdministracionBoxesLayout({ children }) {
  return (
    <RutaProtegida rolesPermitidos={ROLES_PERMITIDOS}>
      {children}
    </RutaProtegida>
  );
}
