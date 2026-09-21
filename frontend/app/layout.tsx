import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "DeepTrace AI | Multimodal Deepfake Forensics Platform",
  description: "AI-Powered Multimodal Deepfake Detection & Digital Forensic Investigation Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-[#FAF5FF] text-[#2D1B46] min-h-screen antialiased flex flex-col">
        <Navbar />
        <div className="flex flex-1">
          <Sidebar />
          <main className="flex-1 overflow-y-auto min-h-[calc(100vh-4rem)] p-6 bg-gradient-to-br from-[#FDF4F8] via-[#FAF5FF] to-[#F5F3FF]">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
