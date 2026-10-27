import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgriVerify | Verification Dashboard",
  description: "Voice-powered crop intelligence and insurance verification.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}

