# Frontend — Sistema Lavadero

Aplicación en Next.js (App Router, JavaScript) y Tailwind CSS. Consume la API REST del backend; la guía general del proyecto está en el [README de la raíz](../README.md).

## Puesta en marcha

```bash
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000 (sin /api)
npm install
npm run dev                  # http://localhost:3000
```

El backend tiene que estar levantado (ver [`backend/README.md`](../backend/README.md)).

## Scripts

| Comando | Qué hace |
|---|---|
| `npm run dev` | Servidor de desarrollo |
| `npm run build` | Build de producción |
| `npm run start` | Sirve el build de producción |
| `npm run lint` | Revisa el código con ESLint |

## Estructura

- `src/app/`: rutas (login, registro, turnos, vehículos, agenda, resumen y `admin/`). Cada ruta restringida por rol tiene un `layout.js` con `RutaProtegida`.
- `src/components/`: componentes compartidos y de turnos.
- `src/lib/`: cliente de la API (`api.js`, con renovación automática del token), sesión y utilidades.

## Despliegue

Vercel, con `frontend` como Root Directory y la variable `NEXT_PUBLIC_API_URL` apuntando a la URL del backend, sin `/api` ni barra final.