import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "SupportIQ",
  description: "AI Customer Support Intelligence Platform",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-muted/30">
        <header className="border-b border-border bg-background">
          <div className="mx-auto flex h-14 w-full max-w-4xl items-center px-6">
            <span className="text-sm font-semibold tracking-tight">SupportIQ</span>
            <span className="ml-auto text-xs text-muted-foreground">
              AI Customer Support Intelligence Platform
            </span>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
