import type { Metadata } from 'next';
import { Inter, Manrope } from 'next/font/google';
import './globals.css';

// 폰트 설정
const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const manrope = Manrope({ subsets: ['latin'], variable: '--font-manrope' });

export const metadata: Metadata = {
  title: 'The Clinical Sanctuary | Medical AI',
  description: 'AI-powered chatbot service for hospital operations',
  keywords: ['hospital', 'chatbot', 'AI', 'health care', 'medical assistant'],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className={`${inter.variable} ${manrope.variable}`}>
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet" />
        {/* eslint-disable-next-line @next/next/no-sync-scripts */}
        <script src="/config.js" />
      </head>
      <body className="antialiased bg-surface text-on-surface">
        {children}
      </body>
    </html>
  );
}
