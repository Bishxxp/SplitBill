import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SplitBill | Shared Expenses",
  description: "Manage and split shared expenses easily.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#f7f8fc] text-slate-900 antialiased">
          {children}
      </body>
    </html>
  );
}
