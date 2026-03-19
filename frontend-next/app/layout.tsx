import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'AI Research PPT Generator',
  description:
    'Transform ArXiv papers and research topics into beautiful, structured PowerPoint presentations powered by AI.',
  keywords: ['AI', 'research', 'PowerPoint', 'ArXiv', 'presentation', 'generator'],
  authors: [{ name: 'AI Research PPT Generator' }],
  openGraph: {
    title: 'AI Research PPT Generator',
    description:
      'Transform ArXiv papers and research topics into beautiful presentations powered by AI.',
    type: 'website',
  },
};

export const viewport: Viewport = {
  themeColor: '#0f172a',
  colorScheme: 'dark',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} dark`}>
      <body className="bg-slate-950 text-slate-100 antialiased min-h-screen">
        <div className="relative min-h-screen">
          {/* Subtle background grid */}
          <div
            className="fixed inset-0 opacity-[0.03] pointer-events-none"
            style={{
              backgroundImage:
                'linear-gradient(rgba(59,130,246,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.5) 1px, transparent 1px)',
              backgroundSize: '64px 64px',
            }}
          />
          {/* Blue ambient glow top */}
          <div
            className="fixed top-0 left-1/2 -translate-x-1/2 w-[900px] h-[300px] opacity-[0.06] pointer-events-none"
            style={{
              background:
                'radial-gradient(ellipse, rgba(59,130,246,0.8) 0%, transparent 70%)',
              filter: 'blur(40px)',
            }}
          />
          <main className="relative z-10">{children}</main>
        </div>
      </body>
    </html>
  );
}
