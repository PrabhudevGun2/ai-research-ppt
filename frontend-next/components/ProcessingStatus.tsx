'use client';

import { useEffect, useState } from 'react';
import {
  Search,
  FileText,
  Cpu,
  Layers,
  Presentation,
  CheckCircle2,
  Loader2,
  Clock,
} from 'lucide-react';
import type { SessionStage } from '@/lib/types';

// ─── Step Config ──────────────────────────────────────────────────────────────

interface Step {
  id: string;
  label: string;
  description: string;
  icon: React.ElementType;
  stages: SessionStage[];
}

const STEPS: Step[] = [
  {
    id: 'input',
    label: 'Input Received',
    description: 'Session created, starting pipeline',
    icon: FileText,
    stages: [],
  },
  {
    id: 'finding',
    label: 'Finding Papers',
    description: 'Searching ArXiv for relevant papers',
    icon: Search,
    stages: ['discovering_papers', 'awaiting_paper_selection'],
  },
  {
    id: 'processing',
    label: 'Processing Paper',
    description: 'Reading and extracting content',
    icon: Cpu,
    stages: ['processing_paper'],
  },
  {
    id: 'synthesizing',
    label: 'Synthesizing',
    description: 'Structuring slides with AI analysis',
    icon: Layers,
    stages: ['synthesizing', 'awaiting_synthesis_review'],
  },
  {
    id: 'building',
    label: 'Building PPT',
    description: 'Generating presentation files',
    icon: Presentation,
    stages: ['generating_ppt', 'awaiting_final_review', 'completed'],
  },
];

// ─── Stage → Step mapping ─────────────────────────────────────────────────────

function getActiveStepIndex(stage: SessionStage): number {
  for (let i = STEPS.length - 1; i >= 0; i--) {
    if (STEPS[i].stages.includes(stage)) return i;
  }
  if (stage === 'resuming') return 2;
  return 0;
}

const STAGE_LABELS: Partial<Record<SessionStage, string>> = {
  discovering_papers: 'Discovering papers on ArXiv…',
  awaiting_paper_selection: 'Papers found — select one to continue',
  processing_paper: 'Reading and processing paper…',
  synthesizing: 'Synthesizing content with AI…',
  awaiting_synthesis_review: 'Synthesis complete — review slides',
  generating_ppt: 'Generating PowerPoint presentation…',
  awaiting_final_review: 'Presentation ready — review & download',
  completed: 'Presentation generated successfully!',
  resuming: 'Resuming workflow…',
  failed: 'An error occurred',
};

// ─── Elapsed Timer ────────────────────────────────────────────────────────────

function useElapsedTime(startMs: number) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startMs) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [startMs]);

  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;
  return minutes > 0
    ? `${minutes}m ${seconds.toString().padStart(2, '0')}s`
    : `${seconds}s`;
}

// ─── Component ────────────────────────────────────────────────────────────────

interface ProcessingStatusProps {
  stage: SessionStage;
  sessionId: string;
}

export default function ProcessingStatus({ stage, sessionId }: ProcessingStatusProps) {
  const [startMs] = useState(() => Date.now());
  const elapsed = useElapsedTime(startMs);
  const activeIdx = getActiveStepIndex(stage);
  const stageLabel = STAGE_LABELS[stage] || stage;

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-16">
      <div className="w-full max-w-lg space-y-8 animate-fade-in">
        {/* Header card */}
        <div className="card-base text-center">
          <div className="flex justify-center mb-4">
            <div className="relative">
              <div className="w-16 h-16 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
              </div>
              {/* Pulsing ring */}
              <div className="absolute inset-0 rounded-full border-2 border-blue-500/20 animate-ping" />
            </div>
          </div>

          <h2 className="text-xl font-bold text-slate-100 mb-2">Processing Your Request</h2>
          <p className="text-slate-400 text-sm leading-relaxed">{stageLabel}</p>

          {/* Elapsed + session info */}
          <div className="flex items-center justify-center gap-4 mt-4 text-xs text-slate-600">
            <span className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" />
              {elapsed}
            </span>
            <span className="text-slate-700">·</span>
            <span className="font-mono truncate max-w-[140px]">
              {sessionId.slice(0, 16)}…
            </span>
          </div>
        </div>

        {/* Progress stepper */}
        <div className="card-base space-y-1 py-5">
          {STEPS.map((step, idx) => {
            const Icon = step.icon;
            const isDone = idx < activeIdx;
            const isActive = idx === activeIdx;
            const isPending = idx > activeIdx;

            return (
              <div key={step.id}>
                <div className="flex items-center gap-4 py-3 px-2 rounded-xl transition-colors">
                  {/* Icon circle */}
                  <div
                    className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-500 ${
                      isDone
                        ? 'bg-emerald-500/20 border-emerald-500/60 text-emerald-400'
                        : isActive
                        ? 'bg-blue-500/20 border-blue-400 text-blue-400 step-active'
                        : 'bg-slate-700/40 border-slate-700 text-slate-600'
                    }`}
                  >
                    {isDone ? (
                      <CheckCircle2 className="w-5 h-5" />
                    ) : isActive ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Icon className="w-5 h-5" />
                    )}
                  </div>

                  {/* Text */}
                  <div className="flex-1 min-w-0">
                    <div
                      className={`text-sm font-semibold transition-colors ${
                        isDone
                          ? 'text-emerald-400'
                          : isActive
                          ? 'text-blue-300'
                          : 'text-slate-600'
                      }`}
                    >
                      {step.label}
                    </div>
                    <div
                      className={`text-xs mt-0.5 transition-colors ${
                        isDone
                          ? 'text-emerald-600'
                          : isActive
                          ? 'text-slate-400'
                          : 'text-slate-700'
                      }`}
                    >
                      {step.description}
                    </div>
                  </div>

                  {/* Status badge */}
                  <div className="shrink-0">
                    {isDone && (
                      <span className="text-xs font-medium text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                        Done
                      </span>
                    )}
                    {isActive && (
                      <span className="text-xs font-medium text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-full">
                        Active
                      </span>
                    )}
                  </div>
                </div>

                {/* Connector line */}
                {idx < STEPS.length - 1 && (
                  <div className="ml-7 w-px h-3 bg-slate-700/50" />
                )}
              </div>
            );
          })}
        </div>

        <p className="text-center text-xs text-slate-600">
          This may take 30–120 seconds depending on paper length and model speed.
          <br />
          You can safely keep this tab open.
        </p>
      </div>
    </div>
  );
}
