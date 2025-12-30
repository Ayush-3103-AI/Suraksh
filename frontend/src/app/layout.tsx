import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { BodyHydrationTracker } from "@/components/body-hydration-tracker";

const inter = Inter({
  subsets: ["latin"],
  weight: ["100", "300", "400", "500", "700"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "SURAKSH Portal - Secure Intelligence Platform",
  description: "Quantum-resilient multi-agency intelligence collaboration",
  icons: {
    icon: [
      { url: "/suraksh_logo.png", type: "image/png" },
      { url: "/favicon.ico", sizes: "any" },
    ],
    shortcut: "/suraksh_logo.png",
    apple: "/suraksh_logo.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} bg-gradient-to-br from-space via-space-50 to-space-100 text-white antialiased font-sans`}
        suppressHydrationWarning={true}
      >
        <BodyHydrationTracker />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

