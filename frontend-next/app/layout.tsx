import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Research PPT Generator',
  description: 'Transform ArXiv papers into beautiful presentations powered by AI.',
  keywords: ['AI', 'research', 'PowerPoint', 'ArXiv', 'presentation'],
  openGraph: {
    title: 'AI Research PPT Generator',
    description: 'Transform ArXiv papers into beautiful presentations powered by AI.',
    type: 'website',
  },
};

export const viewport: Viewport = {
  themeColor: '#ffffff',
  colorScheme: 'light',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-gray-900 antialiased min-h-screen">
        <main>{children}</main>
      </body>
    </html>
  );
}
