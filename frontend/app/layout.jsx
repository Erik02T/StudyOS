import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { StudyOSProvider } from "../components/providers/StudyOSProvider";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-code",
  display: "swap",
});

export const metadata = {
  title: "StudyOS",
  description: "The Operating System for Learning",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${jetbrains.variable}`}>
        <StudyOSProvider>{children}</StudyOSProvider>
      </body>
    </html>
  );
}
