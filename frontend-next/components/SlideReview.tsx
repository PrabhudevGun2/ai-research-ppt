'use client';

import { useState, useCallback } from 'react';
import {
  Layers, ChevronDown, ChevronUp, Pencil, Hash, MessageSquare,
  BarChart2, CheckCircle2, Loader2, AlertCircle, FileText,
  Image, Presentation, Plus, Trash2,
} from 'lucide-react';
import type { SlideContent, SlideType } from '@/lib/types';
import { resumeSession } from '@/lib/api';

const SLIDE_TYPE_STYLES: Record<string, { label: string; color: string; bg: string; border: string }> = {
  title:       { label: 'Title',       color: 'text-violet-700', bg: 'bg-violet-50',  border: 'border-violet-200' },
  problem:     { label: 'Problem',     color: 'text-red-700',    bg: 'bg-red-50',     border: 'border-red-200' },
  motivation:  { label: 'Motivation',  color: 'text-orange-700', bg: 'bg-orange-50',  border: 'border-orange-200' },
  background:  { label: 'Background',  color: 'text-sky-700',    bg: 'bg-sky-50',     border: 'border-sky-200' },
  methodology: { label: 'Methodology', color: 'text-blue-700',   bg: 'bg-blue-50',    border: 'border-blue-200' },
  results:     { label: 'Results',     color: 'text-emerald-700',bg: 'bg-emerald-50', border: 'border-emerald-200' },
  conclusion:  { label: 'Conclusion',  color: 'text-teal-700',   bg: 'bg-teal-50',    border: 'border-teal-200' },
  future_work: { label: 'Future Work', color: 'text-purple-700', bg: 'bg-purple-50',  border: 'border-purple-200' },
  references:  { label: 'References',  color: 'text-gray-600',   bg: 'bg-gray-50',    border: 'border-gray-200' },
  generic:     { label: 'Content',     color: 'text-gray-600',   bg: 'bg-gray-50',    border: 'border-gray-200' },
};

function getStyle(type: string) {
  return SLIDE_TYPE_STYLES[type] || SLIDE_TYPE_STYLES.generic;
}

function StatsBadge({ icon: Icon, label, value, color }: { icon: React.ElementType; label: string; value: number | string; color: string }) {
  return (
    <div className="flex items-center gap-2 bg-white border border-gray-100 rounded-xl px-4 py-3 shadow-sm">
      <Icon className={`w-4 h-4 ${color}`} />
      <div>
        <div className={`text-lg font-bold ${color}`}>{value}</div>
        <div className="text-xs text-gray-400">{label}</div>
      </div>
    </div>
  );
}

function SlideCard({ slide, index, onChange }: { slide: SlideContent; index: number; onChange: (s: SlideContent) => void }) {
  const [expanded, setExpanded] = useState(index === 0);
  const [editingNotes, setEditingNotes] = useState(false);
  const style = getStyle(slide.slide_type);

  return (
    <div className={`bg-white border-2 rounded-2xl overflow-hidden transition-all duration-200 ${
      expanded ? `${style.border} border-l-4` : 'border-gray-100 hover:border-gray-200'
    }`}>
      <button
        className="w-full flex items-center gap-4 p-4 text-left hover:bg-gray-50 transition-colors"
        onClick={() => setExpanded(e => !e)}
      >
        <div className="shrink-0 w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center text-gray-500 text-xs font-bold">
          {slide.order}
        </div>
        <span className={`shrink-0 text-xs font-semibold px-2.5 py-1 rounded-full border ${style.bg} ${style.color} ${style.border}`}>
          {style.label}
        </span>
        <span className="flex-1 text-gray-800 text-sm font-medium truncate">{slide.title || '(Untitled)'}</span>
        <span className="shrink-0 text-xs text-gray-400 hidden sm:block">
          {slide.body_points.length} point{slide.body_points.length !== 1 ? 's' : ''}
        </span>
        {expanded ? <ChevronUp className="shrink-0 w-4 h-4 text-gray-400" /> : <ChevronDown className="shrink-0 w-4 h-4 text-gray-400" />}
      </button>

      {expanded && (
        <div className="px-5 pb-5 space-y-4 border-t border-gray-100 pt-4 animate-fade-in">
          <div>
            <label className="flex items-center gap-1.5 text-xs text-gray-500 font-medium mb-1.5">
              <Pencil className="w-3.5 h-3.5" /> Slide Title
            </label>
            <input type="text" value={slide.title}
              onChange={e => onChange({ ...slide, title: e.target.value })}
              className="input-base text-sm" placeholder="Enter slide title…" />
          </div>

          {slide.subtitle !== undefined && (
            <div>
              <label className="flex items-center gap-1.5 text-xs text-gray-500 font-medium mb-1.5">
                <Hash className="w-3.5 h-3.5" /> Subtitle
              </label>
              <input type="text" value={slide.subtitle || ''}
                onChange={e => onChange({ ...slide, subtitle: e.target.value })}
                className="input-base text-sm" placeholder="Optional subtitle…" />
            </div>
          )}

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="flex items-center gap-1.5 text-xs text-gray-500 font-medium">
                <Layers className="w-3.5 h-3.5" /> Bullet Points
              </label>
              <button onClick={() => onChange({ ...slide, body_points: [...slide.body_points, ''] })}
                className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 transition-colors">
                <Plus className="w-3.5 h-3.5" /> Add point
              </button>
            </div>
            <div className="space-y-2">
              {slide.body_points.map((point, pIdx) => (
                <div key={pIdx} className="flex items-start gap-2">
                  <span className="mt-3 shrink-0 w-1.5 h-1.5 rounded-full bg-blue-400" />
                  <input type="text" value={point}
                    onChange={e => { const u = [...slide.body_points]; u[pIdx] = e.target.value; onChange({ ...slide, body_points: u }); }}
                    className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition-all"
                    placeholder={`Bullet ${pIdx + 1}…`} />
                  <button onClick={() => onChange({ ...slide, body_points: slide.body_points.filter((_, i) => i !== pIdx) })}
                    className="mt-2 text-gray-300 hover:text-red-500 transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
              {slide.body_points.length === 0 && (
                <p className="text-xs text-gray-400 italic py-2">No bullet points — click "Add point".</p>
              )}
            </div>
          </div>

          {(slide.speaker_notes !== undefined || editingNotes) && (
            <div>
              <label className="flex items-center gap-1.5 text-xs text-gray-500 font-medium mb-1.5">
                <MessageSquare className="w-3.5 h-3.5" /> Speaker Notes
              </label>
              <textarea value={slide.speaker_notes || ''}
                onChange={e => onChange({ ...slide, speaker_notes: e.target.value })}
                className="input-base text-sm min-h-[80px] resize-y" placeholder="Notes for presenter…" />
            </div>
          )}
          {slide.speaker_notes === undefined && !editingNotes && (
            <button onClick={() => setEditingNotes(true)}
              className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 transition-colors">
              <MessageSquare className="w-3.5 h-3.5" /> Add speaker notes
            </button>
          )}

          {slide.image_path && (
            <div className="flex items-center gap-2 text-xs text-gray-400 bg-gray-50 rounded-lg px-3 py-2 border border-gray-100">
              <Image className="w-3.5 h-3.5" />
              <span className="truncate">{slide.image_caption || slide.image_path}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function SlideReview({ slides: initialSlides, sessionId }: { slides: SlideContent[]; sessionId: string }) {
  const [slides, setSlides] = useState<SlideContent[]>([...initialSlides].sort((a, b) => a.order - b.order));
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [feedback, setFeedback] = useState('');

  const updateSlide = useCallback((i: number, updated: SlideContent) => {
    setSlides(prev => { const n = [...prev]; n[i] = updated; return n; });
  }, []);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError('');
    try {
      await resumeSession(sessionId, { action: 'approve_slides', approved_slides: slides, feedback_text: feedback.trim() || undefined });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to generate presentation');
      setIsGenerating(false);
    }
  };

  const withImages = slides.filter(s => s.image_path).length;

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-12">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-8 animate-fade-in">
          <div className="inline-flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold px-4 py-2 rounded-full mb-4">
            <CheckCircle2 className="w-3.5 h-3.5" /> Synthesis Complete
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Review Your Slides</h2>
          <p className="text-gray-500 text-sm">Edit any slide before generating the final presentation.</p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          <StatsBadge icon={Presentation} label="Total Slides" value={slides.length} color="text-blue-600" />
          <StatsBadge icon={BarChart2} label="Results" value={slides.filter(s => s.slide_type === 'results').length} color="text-emerald-600" />
          <StatsBadge icon={FileText} label="Methodology" value={slides.filter(s => s.slide_type === 'methodology').length} color="text-purple-600" />
          <StatsBadge icon={Image} label="With Images" value={withImages} color="text-orange-600" />
        </div>

        <div className="space-y-3 mb-8">
          {slides.map((slide, idx) => (
            <SlideCard key={`${slide.order}-${idx}`} slide={slide} index={idx} onChange={u => updateSlide(idx, u)} />
          ))}
        </div>

        <div className="card-base mb-5">
          <label className="flex items-center gap-2 text-sm text-gray-700 font-medium mb-2">
            <MessageSquare className="w-4 h-4 text-gray-400" /> Additional Instructions (optional)
          </label>
          <textarea value={feedback} onChange={e => setFeedback(e.target.value)}
            className="input-base min-h-[80px] resize-y text-sm"
            placeholder="e.g. 'Make it more technical', 'Add more detail on methodology'…" />
        </div>

        {error && (
          <div className="flex items-start gap-3 bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm mb-5">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" /> {error}
          </div>
        )}

        <button onClick={handleGenerate} disabled={isGenerating}
          className="btn-primary w-full flex items-center justify-center gap-3 text-base py-4">
          {isGenerating
            ? <><Loader2 className="w-5 h-5 animate-spin" /> Generating presentation…</>
            : <><Presentation className="w-5 h-5" /> Generate Presentation <CheckCircle2 className="w-5 h-5" /></>}
        </button>
        <p className="text-center text-xs text-gray-400 mt-3">Generates PPTX, DOCX, and PDF versions.</p>
      </div>
    </div>
  );
}
