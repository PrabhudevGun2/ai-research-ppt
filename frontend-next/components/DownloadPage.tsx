'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  CheckCircle2, Download, Presentation, FileText, FileDown,
  Loader2, PartyPopper, Calendar, Layers, Tag, AlertCircle, RotateCcw,
} from 'lucide-react';
import type { GeneratedPPT } from '@/lib/types';
import { downloadPPT, downloadDOCX, downloadPDF, triggerDownload } from '@/lib/api';

function formatDate(iso: string) {
  try { return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }); }
  catch { return iso; }
}

function DownloadCard({ icon: Icon, format, label, description, iconColor, bgColor, borderColor, onDownload, available }: {
  icon: React.ElementType; format: string; label: string; description: string;
  iconColor: string; bgColor: string; borderColor: string;
  onDownload: () => Promise<void>; available: boolean;
}) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle');
  const [errMsg, setErrMsg] = useState('');

  const handleClick = async () => {
    if (!available || status === 'loading') return;
    setStatus('loading'); setErrMsg('');
    try {
      await onDownload();
      setStatus('done');
      setTimeout(() => setStatus('idle'), 3000);
    } catch (err: unknown) {
      setErrMsg(err instanceof Error ? err.message : 'Download failed');
      setStatus('error');
    }
  };

  return (
    <div className={`bg-white border-2 rounded-2xl p-5 flex flex-col gap-4 transition-all ${
      !available ? 'opacity-50' : 'hover:shadow-md'
    } ${status === 'done' ? 'border-emerald-300' : available ? borderColor : 'border-gray-100'}`}>
      <div className={`self-start p-3 rounded-xl ${bgColor}`}>
        <Icon className={`w-6 h-6 ${iconColor}`} />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-lg font-bold ${iconColor}`}>{format}</span>
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${bgColor} ${iconColor} ${borderColor}`}>{label}</span>
        </div>
        <p className="text-gray-400 text-sm leading-snug">{description}</p>
      </div>
      {status === 'error' && (
        <div className="flex items-start gap-2 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg p-2">
          <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" /> {errMsg}
        </div>
      )}
      <button onClick={handleClick} disabled={!available || status === 'loading'}
        className={`w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-semibold text-sm transition-all ${
          status === 'done'   ? 'bg-emerald-600 text-white'
          : available         ? 'bg-gray-900 hover:bg-gray-800 text-white disabled:opacity-50'
          : 'bg-gray-100 text-gray-400 cursor-not-allowed'
        }`}>
        {status === 'loading' ? <><Loader2 className="w-4 h-4 animate-spin" /> Downloading…</>
          : status === 'done'  ? <><CheckCircle2 className="w-4 h-4" /> Downloaded!</>
          : available          ? <><Download className="w-4 h-4" /> Download {format}</>
          : 'Not available'}
      </button>
    </div>
  );
}

export default function DownloadPage({ generatedPpt, sessionId }: { generatedPpt: GeneratedPPT; sessionId: string }) {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-12">
      <div className="max-w-3xl mx-auto">

        {/* Success banner */}
        <div className="bg-emerald-50 border-2 border-emerald-200 rounded-2xl overflow-hidden mb-8 animate-fade-in">
          <div className="flex flex-col sm:flex-row items-center gap-5 p-6">
            <div className="shrink-0 flex items-center justify-center w-16 h-16 rounded-full bg-emerald-100 border-2 border-emerald-300">
              <PartyPopper className="w-8 h-8 text-emerald-600" />
            </div>
            <div className="text-center sm:text-left">
              <h2 className="text-2xl font-bold text-emerald-800 mb-1">Presentation Ready!</h2>
              <p className="text-emerald-600 text-sm">Your research has been transformed into a structured presentation.</p>
            </div>
          </div>
          <div className="border-t border-emerald-200 px-6 py-4 flex flex-wrap gap-x-6 gap-y-2 bg-emerald-50/50">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Layers className="w-4 h-4 text-emerald-600" />
              <span><span className="font-semibold text-gray-900">{generatedPpt.slide_count}</span> slides</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Calendar className="w-4 h-4 text-emerald-600" />
              <span>{formatDate(generatedPpt.generated_at)}</span>
            </div>
            {generatedPpt.topics_covered.length > 0 && (
              <div className="flex items-center gap-2 text-sm text-gray-600 flex-wrap">
                <Tag className="w-4 h-4 text-emerald-600 shrink-0" />
                {generatedPpt.topics_covered.slice(0, 2).map(t => (
                  <span key={t} className="bg-emerald-100 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full text-xs">{t.slice(0, 60)}</span>
                ))}
              </div>
            )}
          </div>
        </div>

        <h3 className="text-gray-700 font-semibold text-sm uppercase tracking-wider mb-4">Download Formats</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <DownloadCard
            icon={Presentation} format="PPTX" label="PowerPoint"
            description="Open with Microsoft PowerPoint, Google Slides, or Keynote."
            iconColor="text-orange-600" bgColor="bg-orange-50" borderColor="border-orange-200"
            onDownload={async () => { const b = await downloadPPT(sessionId); triggerDownload(b, `presentation-${sessionId.slice(0,8)}.pptx`); }}
            available={Boolean(generatedPpt.file_path)} />
          <DownloadCard
            icon={FileText} format="DOCX" label="Word Document"
            description="Full document with slides as formatted pages. Great for editing."
            iconColor="text-blue-600" bgColor="bg-blue-50" borderColor="border-blue-200"
            onDownload={async () => { const b = await downloadDOCX(sessionId); triggerDownload(b, `presentation-${sessionId.slice(0,8)}.docx`); }}
            available={Boolean(generatedPpt.doc_path)} />
          <DownloadCard
            icon={FileDown} format="PDF" label="PDF Report"
            description="Portable format for sharing. Preserves all formatting."
            iconColor="text-red-600" bgColor="bg-red-50" borderColor="border-red-200"
            onDownload={async () => { const b = await downloadPDF(sessionId); triggerDownload(b, `presentation-${sessionId.slice(0,8)}.pdf`); }}
            available={Boolean(generatedPpt.pdf_path)} />
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <button onClick={() => router.push('/')}
            className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-sm">
            <RotateCcw className="w-4 h-4" /> Generate Another Presentation
          </button>
        </div>

        <p className="text-center text-xs text-gray-300 mt-6 font-mono">{sessionId}</p>
      </div>
    </div>
  );
}
