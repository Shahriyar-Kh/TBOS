// ============================================================
// app/layout.tsx — Root layout
// ============================================================

import type { Metadata, Viewport } from "next";
import { DM_Sans, Syne, JetBrains_Mono } from "next/font/google";
import { Providers } from "@/components/Providers";
import "./globals.css";

// ── Fonts ────────────────────────────────────────────────────
const dmSans = DM_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-dm-sans",
  weight: ["300", "400", "500", "600", "700"],
});

const syne = Syne({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-syne",
  weight: ["400", "600", "700", "800"],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-jetbrains-mono",
  weight: ["400", "500"],
});

// ── Metadata ──────────────────────────────────────────────────
export const metadata: Metadata = {
  title: {
    default: "TechBuilt Open School",
    template: "%s | TechBuilt Open School",
  },
  description:
    "A world-class open learning platform for students, instructors, and administrators.",
  keywords: ["LMS", "online learning", "courses", "education", "TechBuilt"],
  authors: [{ name: "TechBuilt" }],
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000"
  ),
  openGraph: {
    type: "website",
    siteName: "TechBuilt Open School",
    title: "TechBuilt Open School",
    description: "A world-class open learning platform",
  },
  twitter: {
    card: "summary_large_image",
    title: "TechBuilt Open School",
    description: "A world-class open learning platform",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0f172a" },
  ],
  width: "device-width",
  initialScale: 1,
};

// ── Root Layout ───────────────────────────────────────────────
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${dmSans.variable} ${syne.variable} ${jetbrainsMono.variable}`}
    >
      <body className="min-h-screen bg-background font-sans text-foreground antialiased selection:bg-brand-200 selection:text-brand-900">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
