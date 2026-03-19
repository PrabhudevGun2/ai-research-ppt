'use client';

import { useEffect, useState } from 'react';
import { Search, FileText, Cpu, Layers, Presentation, CheckCircle2, Loader2, Clock } from 'lucide-react';
import type { SessionStage } from '@/lib/types';

interface Step {
  id: string;
  label: string;
  description: string;
  icon: React.ElementType;
  stages: SessionStage[];
}

const STEPS: Step[] = [
  { id: 'input',       label: 'Input Received',   description: 'Session created, starting pipeline',       icon: FileText,     stages: [] },
  { id: 'finding',     label: 'Finding Papers',    description: 'Searching ArXiv for relevant papers',      icon: Search,       stages: ['discovering_papers', 'awaiting_paper_selection'] },
  { id: 'processing',  label: 'Processing Paper',  description: 'Reading and extracting content',           icon: Cpu,          stages: ['processing_paper'] },
  { id: 'synthesizing',label: 'Synthesizing',      description: 'Structuring slides with AI analysis',      icon: Layers,       stages: ['synthesizing', 'awaiting_synthesis_review'] },
  { id: 'building',    label: 'Building PPT',      description: 'Generating presentation files',            icon: Presentation, stages: ['generating_ppt', 'awaiting_final_review', 'completed'] },
];

function getActiveStepIndex(stage: SessionStage): number {
  for (let i = STEPS.length - 1; i >= 0; i--) {
    if (STEPS[i].stages.includes(stage)) return i;
  }
  if (stage === 'resuming') return 2;
  return 0;
}

const STAGE_LABELS: Partial<Record<SessionStage, string>> = {
  discovering_papers:      'Searching ArXiv for papers…',
  awaiting_paper_selection:'Papers found — select one to continue',
  processing_paper:        'Reading and processing the paper…',
  synthesizing:            'Synthesizing slide content with AI…',
  awaiting_synthesis_review:'Synthesis complete — review your slides',
  generating_ppt:          'Generating PowerPoint presentation…',
  awaiting_final_review:   'Presentation ready — review & download',
  completed:               'Done! Your presentation is ready.',
  resuming:                'Resuming workflow…',
  failed:                  'An error occurred',
};

function useElapsed(startMs: number) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - startMs) / 1000)), 1000);
    return () => clearInterval(id);
  }, [startMs]);
  const m = Math.floor(elapsed / 60), s = elapsed % 60;
  return m > 0 ? `${m}m ${s.toString().padStart(2, '0')}s` : `${s}s`;
}

export default function ProcessingStatus({ stage, sessionId }: { stage: SessionStage; sessionId: string }) {
  const [startMs] = useState(() => Date.now());
  const elapsed = useElapsed(startMs);
  const activeIdx = getActiveStepIndex(stage);
  const stageLabel = STAGE_LABELS[stage] || stage;

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-16">
      <div className="w-full max-w-md space-y-6 animate-fade-in">

        {/* Status card */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 text-center">
          <div className="flex justify-center mb-5">
            <div className="relative">
              <div className="w-16 h-16 rounded-full bg-blue-50 border-2 border-blue-200 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
              </div>
              <div className="absolute inset-0 rounded-full border-2 border-blue-300 animate-ping opacity-30" />
            </div>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Processing Your Request</h2>
          <p className="text-gray-500 text-sm leading-relaxed">{stageLabel}</p>
          <div className="flex items-center justify-center gap-4 mt-4 text-xs text-gray-400">
            <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" />{elapsed}</span>
            <span>·</span>
            <span className="font-mono">{sessionId.slice(0, 12)}…</span>
          </div>
        </div>

        {/* Stepper */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-1">
          {STEPS.map((step, idx) => {
            const Icon = step.icon;
            const isDone = idx < activeIdx;
            const isActive = idx === activeIdx;
            return (
              <div key={step.id}>
                <div className="flex items-center gap-4 py-3 px-2 rounded-xl">
                  <div className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-500 ${
                    isDone    ? 'bg-emerald-50 border-emerald-300 text-emerald-600'
                    : isActive ? 'bg-blue-50 border-blue-400 text-blue-600 step-active'
                    : 'bg-gray-50 border-gray-200 text-gray-400'
                  }`}>
                    {isDone ? <CheckCircle2 className="w-5 h-5" />
                      : isActive ? <Loader2 className="w-5 h-5 animate-spin" />
                      : <Icon className="w-5 h-5" />}
                  </div>
                  <div className="flex-1">
                    <div className={`text-sm font-semibold ${isDone ? 'text-emerald-600' : isActive ? 'text-blue-700' : 'text-gray-400'}`}>
                      {step.label}
                    </div>
                    <div className={`text-xs mt-0.5 ${isDone ? 'text-emerald-500' : isActive ? 'text-gray-500' : 'text-gray-300'}`}>
                      {step.description}
                    </div>
                  </div>
                  <div className="shrink-0">
                    {isDone && <span className="text-xs font-medium text-emerald-600 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">Done</span>}
                    {isActive && <span className="text-xs font-medium text-blue-600 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded-full">Active</span>}
                  </div>
                </div>
                {idx < STEPS.length - 1 && <div className="ml-7 w-px h-3 bg-gray-100" />}
              </div>
            );
          })}
        </div>

        <p className="text-center text-xs text-gray-400">
          Takes 30–120 seconds depending on paper length.<br />You can safely keep this tab open.
        </p>
      </div>
    </div>
  );
}
