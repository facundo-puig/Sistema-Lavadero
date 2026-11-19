"use client";

import RutaProtegida from "@/components/RutaProtegida";

const ROLES_PERMITIDOS = ["ADMINISTRADOR", "OPERARIO"];

export default function AgendaLayout({ children }) {
    return (
        <RutaProtegida rolesPermitidos={ROLES_PERMITIDOS}>
            {children}
        </RutaProtegida>
    );
}