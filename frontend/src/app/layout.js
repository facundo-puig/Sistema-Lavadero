
import { Geist, Geist_Mono } from "next/font/google";
import { Toaster } from "sonner";

import SesionHeader from "@/components/SesionHeader";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "Sistema Lavadero",
  description: "Gestión de turnos para lavadero de vehículos",
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="es"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-gray-50 text-gray-900">
        <header className="border-b bg-white">
          <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4 px-4 py-3">
            <span className="font-semibold">
              Sistema Lavadero
            </span>

            <SesionHeader />
          </div>
        </header>

        <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6">
          {children}
        </main>

        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}
