'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { AlertTriangle, RotateCcw, Home } from 'lucide-react';

import { getSessionStatus } from '@/lib/api';
import type { SessionStatus, SessionStage } from '@/lib/types';

import ProcessingStatus from '@/components/ProcessingStatus';
import PaperList from '@/components/PaperList';
import SlideReview from '@/components/SlideReview';
import DownloadPage from '@/components/DownloadPage';

// ─── Constants ────────────────────────────────────────────────────────────────

/** Stages that need continuous polling */
const POLLING_STAGES: SessionStage[] = [
  'discovering_papers',
  'processing_paper',
  'synthesizing',
  'generating_ppt',
  'resuming',
];

const POLL_INTERVAL_MS = 2000;

// ─── Error State ──────────────────────────────────────────────────────────────

function ErrorState({
  message,
  sessionId,
  onRetry,
}: {
  message: string;
  sessionId: string;
  onRetry: () => void;
}) {
  const router = useRouter();
  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-md w-full text-center space-y-6 animate-fade-in">
        <div className="flex justify-center">
          <div className="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center">
            <AlertTriangle className="w-8 h-8 text-red-400" />
          </div>
        </div>

        <div>
          <h2 className="text-2xl font-bold text-slate-100 mb-2">Something went wrong</h2>
          <p className="text-slate-400 text-sm leading-relaxed">{message}</p>
          <p className="text-slate-600 text-xs mt-3 font-mono">Session: {sessionId}</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={onRetry}
            className="flex items-center justify-center gap-2 bg-slate-700 hover:bg-slate-600 text-slate-200 font-medium py-2.5 px-5 rounded-xl border border-slate-600 transition-all"
          >
            <RotateCcw className="w-4 h-4" />
            Retry
          </button>
          <button
            onClick={() => router.push('/')}
            className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2.5 px-5 rounded-xl transition-all"
          >
            <Home className="w-4 h-4" />
            Start Over
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Loading Skeleton ─────────────────────────────────────────────────────────

function InitialLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="flex flex-col items-center gap-4 animate-fade-in">
        <div className="w-12 h-12 rounded-full border-2 border-blue-500/30 border-t-blue-500 animate-spin" />
        <p className="text-slate-500 text-sm">Connecting to session…</p>
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function SessionPage() {
  const params = useParams();
  const sessionId = params.id as string;

  const [status, setStatus] = useState<SessionStatus | null>(null);
  const [fetchError, setFetchError] = useState('');
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMountedRef = useRef(true);

  const poll = useCallback(async () => {
    try {
      const data = await getSessionStatus(sessionId);
      if (!isMountedRef.current) return;
      setStatus(data);
      setFetchError('');
      setIsInitialLoad(false);

      // Continue polling if in an active processing stage
      if (POLLING_STAGES.includes(data.stage)) {
        pollRef.current = setTimeout(poll, POLL_INTERVAL_MS);
      }
    } catch (err: unknown) {
      if (!isMountedRef.current) return;
      const msg = err instanceof Error ? err.message : 'Failed to fetch session status';
      setFetchError(msg);
      setIsInitialLoad(false);
      // Retry after a longer delay on error
      pollRef.current = setTimeout(poll, POLL_INTERVAL_MS * 3);
    }
  }, [sessionId]);

  useEffect(() => {
    isMountedRef.current = true;
    poll();
    return () => {
      isMountedRef.current = false;
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, [poll]);

  // Resume polling when stage changes to a polling stage
  useEffect(() => {
    if (!status) return;
    if (POLLING_STAGES.includes(status.stage)) {
      if (!pollRef.current) {
        pollRef.current = setTimeout(poll, POLL_INTERVAL_MS);
      }
    } else {
      if (pollRef.current) {
        clearTimeout(pollRef.current);
        pollRef.current = null;
      }
    }
  }, [status?.stage, poll]);

  // ── Render ──────────────────────────────────────────────────────────────────

  if (isInitialLoad) {
    return <InitialLoader />;
  }

  if (fetchError && !status) {
    return (
      <ErrorState
        message={fetchError}
        sessionId={sessionId}
        onRetry={() => {
          setFetchError('');
          setIsInitialLoad(true);
          poll();
        }}
      />
    );
  }

  if (!status) return <InitialLoader />;

  const { stage, interrupt_payload, error } = status;

  // Failed state
  if (stage === 'failed') {
    return (
      <ErrorState
        message={error || 'The session failed unexpectedly. Please try again.'}
        sessionId={sessionId}
        onRetry={() => {
          setFetchError('');
          poll();
        }}
      />
    );
  }

  // Paper selection
  if (stage === 'awaiting_paper_selection') {
    const papers = interrupt_payload?.papers ?? [];
    if (papers.length === 0) {
      return (
        <ProcessingStatus stage={stage} sessionId={sessionId} />
      );
    }
    return <PaperList papers={papers} sessionId={sessionId} />;
  }

  // Slide review
  if (stage === 'awaiting_synthesis_review') {
    const slides = interrupt_payload?.slides ?? [];
    if (slides.length === 0) {
      return <ProcessingStatus stage={stage} sessionId={sessionId} />;
    }
    return <SlideReview slides={slides} sessionId={sessionId} />;
  }

  // Download / final review
  if (stage === 'awaiting_final_review' || stage === 'completed') {
    const generatedPpt = interrupt_payload?.generated_ppt;
    if (!generatedPpt) {
      return <ProcessingStatus stage={stage} sessionId={sessionId} />;
    }
    return <DownloadPage generatedPpt={generatedPpt} sessionId={sessionId} />;
  }

  // All other stages: processing animation
  return <ProcessingStatus stage={stage} sessionId={sessionId} />;
}
