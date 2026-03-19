'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  CheckCircle2,
  Download,
  Presentation,
  FileText,
  FileDown,
  Loader2,
  PartyPopper,
  Calendar,
  Layers,
  Tag,
  ArrowLeft,
  AlertCircle,
  RotateCcw,
} from 'lucide-react';
import type { GeneratedPPT } from '@/lib/types';
import { downloadPPT, downloadDOCX, downloadPDF, triggerDownload } from '@/lib/api';

// ─── Format helpers ───────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

// ─── Download Card ────────────────────────────────────────────────────────────

interface DownloadCardProps {
  icon: React.ElementType;
  format: string;
  label: string;
  description: string;
  color: string;
  bgColor: string;
  borderColor: string;
  onDownload: () => Promise<void>;
  available: boolean;
}

function DownloadCard({
  icon: Icon,
  format,
  label,
  description,
  color,
  bgColor,
  borderColor,
  onDownload,
  available,
}: DownloadCardProps) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState('');

  const handleClick = async () => {
    if (!available || status === 'loading') return;
    setStatus('loading');
    setErrorMsg('');
    try {
      await onDownload();
      setStatus('done');
      // Reset after 3s
      setTimeout(() => setStatus('idle'), 3000);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Download failed');
      setStatus('error');
    }
  };

  return (
    <div
      className={`card-base flex flex-col gap-4 card-hover ${
        !available ? 'opacity-50' : ''
      } ${
        status === 'done'
          ? 'border-emerald-500/40 shadow-green-glow'
          : borderColor
      }`}
    >
      {/* Icon */}
      <div className={`self-start p-3 rounded-xl ${bgColor}`}>
        <Icon className={`w-6 h-6 ${color}`} />
      </div>

      {/* Info */}
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-lg font-bold ${color}`}>{format}</span>
          <span
            className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${bgColor} ${color} ${borderColor}`}
          >
            {label}
          </span>
        </div>
        <p className="text-slate-400 text-sm leading-snug">{description}</p>
      </div>

      {/* Error */}
      {status === 'error' && (
        <div className="flex items-start gap-2 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-2">
          <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
          {errorMsg}
        </div>
      )}

      {/* Button */}
      <button
        onClick={handleClick}
        disabled={!available || status === 'loading'}
        className={`w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-semibold text-sm transition-all duration-200 ${
          status === 'done'
            ? 'bg-emerald-600 text-white border border-emerald-500'
            : available
            ? `bg-slate-700 hover:bg-slate-600 text-slate-200 border border-slate-600 hover:${borderColor}`
            : 'bg-slate-800 text-slate-600 border border-slate-700 cursor-not-allowed'
        }`}
      >
        {status === 'loading' ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Downloading…
          </>
        ) : status === 'done' ? (
          <>
            <CheckCircle2 className="w-4 h-4" />
            Downloaded!
          </>
        ) : available ? (
          <>
            <Download className="w-4 h-4" />
            Download {format}
          </>
        ) : (
          'Not available'
        )}
      </button>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

interface DownloadPageProps {
  generatedPpt: GeneratedPPT;
  sessionId: string;
}

export default function DownloadPage({ generatedPpt, sessionId }: DownloadPageProps) {
  const router = useRouter();

  const hasPptx = Boolean(generatedPpt.file_path);
  const hasDocx = Boolean(generatedPpt.doc_path);
  const hasPdf = Boolean(generatedPpt.pdf_path);

  const handleDownloadPPTX = async () => {
    const blob = await downloadPPT(sessionId);
    triggerDownload(blob, `presentation-${sessionId.slice(0, 8)}.pptx`);
  };

  const handleDownloadDOCX = async () => {
    const blob = await downloadDOCX(sessionId);
    triggerDownload(blob, `presentation-${sessionId.slice(0, 8)}.docx`);
  };

  const handleDownloadPDF = async () => {
    const blob = await downloadPDF(sessionId);
    triggerDownload(blob, `presentation-${sessionId.slice(0, 8)}.pdf`);
  };

  return (
    <div className="min-h-screen px-6 py-12">
      <div className="max-w-3xl mx-auto">
        {/* Success banner */}
        <div
          className="rounded-2xl border border-emerald-500/25 overflow-hidden mb-10 animate-fade-in"
          style={{
            background:
              'linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(5,150,105,0.05) 100%)',
          }}
        >
          <div className="flex flex-col sm:flex-row items-center gap-5 p-6">
            {/* Big check icon */}
            <div className="shrink-0 flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/15 border border-emerald-500/30">
              <PartyPopper className="w-8 h-8 text-emerald-400" />
            </div>
            <div className="text-center sm:text-left">
              <h2 className="text-2xl font-bold text-emerald-300 mb-1">
                Presentation Ready!
              </h2>
              <p className="text-emerald-600 text-sm">
                Your research has been transformed into a structured presentation.
                Download below in your preferred format.
              </p>
            </div>
          </div>

          {/* Presentation stats */}
          <div className="border-t border-emerald-500/15 px-6 py-4 flex flex-wrap gap-x-6 gap-y-2">
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Layers className="w-4 h-4 text-emerald-500" />
              <span>
                <span className="font-semibold text-slate-200">{generatedPpt.slide_count}</span>{' '}
                slides
              </span>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Calendar className="w-4 h-4 text-emerald-500" />
              <span>{formatDate(generatedPpt.generated_at)}</span>
            </div>
            {generatedPpt.topics_covered.length > 0 && (
              <div className="flex items-center gap-2 text-sm text-slate-400 flex-wrap">
                <Tag className="w-4 h-4 text-emerald-500 shrink-0" />
                <span className="flex flex-wrap gap-1">
                  {generatedPpt.topics_covered.slice(0, 5).map((topic) => (
                    <span
                      key={topic}
                      className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full text-xs"
                    >
                      {topic}
                    </span>
                  ))}
                  {generatedPpt.topics_covered.length > 5 && (
                    <span className="text-slate-600 text-xs">
                      +{generatedPpt.topics_covered.length - 5} more
                    </span>
                  )}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Download cards */}
        <h3 className="text-slate-300 font-semibold text-sm uppercase tracking-wider mb-4">
          Download Formats
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          <DownloadCard
            icon={Presentation}
            format="PPTX"
            label="PowerPoint"
            description="Native PowerPoint format. Open with Microsoft PowerPoint, Google Slides, or Keynote."
            color="text-orange-400"
            bgColor="bg-orange-500/10"
            borderColor="border-orange-500/30"
            onDownload={handleDownloadPPTX}
            available={hasPptx}
          />
          <DownloadCard
            icon={FileText}
            format="DOCX"
            label="Word Document"
            description="Full document format with slides as formatted pages. Great for printing and editing."
            color="text-blue-400"
            bgColor="bg-blue-500/10"
            borderColor="border-blue-500/30"
            onDownload={handleDownloadDOCX}
            available={hasDocx}
          />
          <DownloadCard
            icon={FileDown}
            format="PDF"
            label="PDF"
            description="Portable format for sharing and viewing anywhere. Preserves all formatting."
            color="text-red-400"
            bgColor="bg-red-500/10"
            borderColor="border-red-500/30"
            onDownload={handleDownloadPDF}
            available={hasPdf}
          />
        </div>

        {/* Action buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={() => router.push('/')}
            className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 hover:shadow-blue-glow"
          >
            <RotateCcw className="w-4 h-4" />
            Generate Another Presentation
          </button>
          <button
            onClick={() => router.back()}
            className="btn-secondary flex items-center justify-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
        </div>

        <p className="text-center text-xs text-slate-700 mt-6">
          Session ID: <span className="font-mono">{sessionId}</span>
        </p>
      </div>
    </div>
  );
}
