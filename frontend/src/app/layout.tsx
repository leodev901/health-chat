import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Hospital Chatbot Service',
  description: 'AI-powered chatbot service for hospital operations',
  keywords: ['hospital', 'chatbot', 'AI', 'health care', 'medical assistant'],
  openGraph: {
    title: 'Hospital Chatbot Service',
    description: 'AI-powered chatbot service for hospital operations',
    type: 'website',
    locale: 'ko_KR',
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
