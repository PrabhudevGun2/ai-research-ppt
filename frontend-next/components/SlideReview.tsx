'use client';

import { useState, useCallback } from 'react';
import {
  Layers,
  ChevronDown,
  ChevronUp,
  Pencil,
  Hash,
  MessageSquare,
  BarChart2,
  CheckCircle2,
  Loader2,
  AlertCircle,
  FileText,
  Image,
  Presentation,
  Plus,
  Trash2,
} from 'lucide-react';
import type { SlideContent, SlideType } from '@/lib/types';
import { resumeSession } from '@/lib/api';

// ─── Slide Type Styling ───────────────────────────────────────────────────────

const SLIDE_TYPE_STYLES: Record<
  SlideType,
  { label: string; color: string; bg: string; border: string }
> = {
  title: {
    label: 'Title',
    color: 'text-violet-400',
    bg: 'bg-violet-500/10',
    border: 'border-violet-500/30',
  },
  problem: {
    label: 'Problem',
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
  },
  motivation: {
    label: 'Motivation',
    color: 'text-orange-400',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
  },
  background: {
    label: 'Background',
    color: 'text-sky-400',
    bg: 'bg-sky-500/10',
    border: 'border-sky-500/30',
  },
  methodology: {
    label: 'Methodology',
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
  },
  results: {
    label: 'Results',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
  },
  conclusion: {
    label: 'Conclusion',
    color: 'text-teal-400',
    bg: 'bg-teal-500/10',
    border: 'border-teal-500/30',
  },
  future_work: {
    label: 'Future Work',
    color: 'text-purple-400',
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/30',
  },
  references: {
    label: 'References',
    color: 'text-slate-400',
    bg: 'bg-slate-700/30',
    border: 'border-slate-600/40',
  },
  generic: {
    label: 'Generic',
    color: 'text-slate-400',
    bg: 'bg-slate-700/30',
    border: 'border-slate-600/40',
  },
};

function getSlideStyle(type: SlideType) {
  return SLIDE_TYPE_STYLES[type] || SLIDE_TYPE_STYLES.generic;
}

// ─── Stats Bar ────────────────────────────────────────────────────────────────

function countSlidesByType(slides: SlideContent[], type: SlideType) {
  return slides.filter((s) => s.slide_type === type).length;
}

interface StatsBadgeProps {
  icon: React.ElementType;
  label: string;
  value: number | string;
  color?: string;
}

function StatsBadge({ icon: Icon, label, value, color = 'text-blue-400' }: StatsBadgeProps) {
  return (
    <div className="flex items-center gap-2 bg-slate-700/40 border border-slate-700 rounded-xl px-4 py-2.5">
      <Icon className={`w-4 h-4 ${color}`} />
      <div>
        <div className={`text-lg font-bold ${color}`}>{value}</div>
        <div className="text-xs text-slate-500">{label}</div>
      </div>
    </div>
  );
}

// ─── Single Slide Card ────────────────────────────────────────────────────────

interface SlideCardProps {
  slide: SlideContent;
  index: number;
  onChange: (updated: SlideContent) => void;
}

function SlideCard({ slide, index, onChange }: SlideCardProps) {
  const [expanded, setExpanded] = useState(index === 0);
  const [editingNotes, setEditingNotes] = useState(false);

  const style = getSlideStyle(slide.slide_type);

  // Parse body_points from textarea string
  const bodyText = slide.body_points.join('\n');

  const handleBodyChange = (text: string) => {
    onChange({
      ...slide,
      body_points: text
        .split('\n')
        .map((l) => l.trim())
        .filter((l) => l.length > 0),
    });
  };

  const handleAddPoint = () => {
    onChange({ ...slide, body_points: [...slide.body_points, ''] });
  };

  const handleRemovePoint = (idx: number) => {
    const updated = slide.body_points.filter((_, i) => i !== idx);
    onChange({ ...slide, body_points: updated });
  };

  const handlePointChange = (idx: number, val: string) => {
    const updated = [...slide.body_points];
    updated[idx] = val;
    onChange({ ...slide, body_points: updated });
  };

  return (
    <div
      className={`bg-slate-800 border rounded-2xl overflow-hidden transition-all duration-200 ${
        expanded ? `border-l-4 ${style.border} border-slate-700` : 'border-slate-700'
      }`}
    >
      {/* Card header — click to expand */}
      <button
        className="w-full flex items-center gap-4 p-4 text-left hover:bg-slate-700/30 transition-colors"
        onClick={() => setExpanded((e) => !e)}
      >
        {/* Slide number */}
        <div className="shrink-0 w-8 h-8 rounded-lg bg-slate-700/60 border border-slate-600 flex items-center justify-center text-slate-400 text-xs font-bold">
          {slide.order}
        </div>

        {/* Type badge */}
        <span
          className={`shrink-0 text-xs font-semibold px-2.5 py-1 rounded-full border ${style.bg} ${style.color} ${style.border}`}
        >
          {style.label}
        </span>

        {/* Title */}
        <span className="flex-1 text-slate-200 text-sm font-medium truncate">
          {slide.title || '(Untitled)'}
        </span>

        {/* Points count */}
        <span className="shrink-0 text-xs text-slate-500 hidden sm:block">
          {slide.body_points.length} point{slide.body_points.length !== 1 ? 's' : ''}
        </span>

        {/* Expand icon */}
        {expanded ? (
          <ChevronUp className="shrink-0 w-4 h-4 text-slate-500" />
        ) : (
          <ChevronDown className="shrink-0 w-4 h-4 text-slate-500" />
        )}
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="px-5 pb-5 space-y-4 border-t border-slate-700/50 pt-4 animate-fade-in">
          {/* Title input */}
          <div>
            <label className="flex items-center gap-1.5 text-xs text-slate-400 font-medium mb-1.5">
              <Pencil className="w-3.5 h-3.5" />
              Slide Title
            </label>
            <input
              type="text"
              value={slide.title}
              onChange={(e) => onChange({ ...slide, title: e.target.value })}
              className="input-base text-sm"
              placeholder="Enter slide title…"
            />
          </div>

          {/* Subtitle (if present) */}
          {slide.subtitle !== undefined && (
            <div>
              <label className="flex items-center gap-1.5 text-xs text-slate-400 font-medium mb-1.5">
                <Hash className="w-3.5 h-3.5" />
                Subtitle
              </label>
              <input
                type="text"
                value={slide.subtitle || ''}
                onChange={(e) => onChange({ ...slide, subtitle: e.target.value })}
                className="input-base text-sm"
                placeholder="Optional subtitle…"
              />
            </div>
          )}

          {/* Body points — individual editable lines */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
                <Layers className="w-3.5 h-3.5" />
                Bullet Points
              </label>
              <button
                onClick={handleAddPoint}
                className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                Add point
              </button>
            </div>
            <div className="space-y-2">
              {slide.body_points.map((point, pIdx) => (
                <div key={pIdx} className="flex items-start gap-2">
                  <span className="mt-2.5 shrink-0 w-1.5 h-1.5 rounded-full bg-blue-500/60" />
                  <input
                    type="text"
                    value={point}
                    onChange={(e) => handlePointChange(pIdx, e.target.value)}
                    className="flex-1 bg-slate-700/50 border border-slate-600/60 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-blue-500/50 transition-all"
                    placeholder={`Bullet point ${pIdx + 1}…`}
                  />
                  <button
                    onClick={() => handleRemovePoint(pIdx)}
                    className="mt-2 text-slate-600 hover:text-red-400 transition-colors"
                    aria-label="Remove point"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
              {slide.body_points.length === 0 && (
                <p className="text-xs text-slate-600 italic py-2">No bullet points — click "Add point" above.</p>
              )}
            </div>
          </div>

          {/* Speaker notes */}
          {(slide.speaker_notes !== undefined || editingNotes) && (
            <div>
              <label className="flex items-center gap-1.5 text-xs text-slate-400 font-medium mb-1.5">
                <MessageSquare className="w-3.5 h-3.5" />
                Speaker Notes
              </label>
              <textarea
                value={slide.speaker_notes || ''}
                onChange={(e) => onChange({ ...slide, speaker_notes: e.target.value })}
                className="input-base text-sm min-h-[80px] resize-y"
                placeholder="Notes for the presenter…"
              />
            </div>
          )}
          {slide.speaker_notes === undefined && !editingNotes && (
            <button
              onClick={() => setEditingNotes(true)}
              className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-400 transition-colors"
            >
              <MessageSquare className="w-3.5 h-3.5" />
              Add speaker notes
            </button>
          )}

          {/* Image info */}
          {slide.image_path && (
            <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-700/30 rounded-lg px-3 py-2">
              <Image className="w-3.5 h-3.5" />
              <span className="truncate">{slide.image_caption || slide.image_path}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

interface SlideReviewProps {
  slides: SlideContent[];
  sessionId: string;
}

export default function SlideReview({ slides: initialSlides, sessionId }: SlideReviewProps) {
  const [slides, setSlides] = useState<SlideContent[]>(
    [...initialSlides].sort((a, b) => a.order - b.order)
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [feedback, setFeedback] = useState('');

  const updateSlide = useCallback((index: number, updated: SlideContent) => {
    setSlides((prev) => {
      const next = [...prev];
      next[index] = updated;
      return next;
    });
  }, []);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError('');
    try {
      await resumeSession(sessionId, {
        action: 'approve_slides',
        approved_slides: slides,
        feedback_text: feedback.trim() || undefined,
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to generate presentation');
      setIsGenerating(false);
    }
  };

  // Stats
  const totalSlides = slides.length;
  const resultSlides = countSlidesByType(slides, 'results');
  const methodSlides = countSlidesByType(slides, 'methodology');
  const withImages = slides.filter((s) => s.image_path).length;

  return (
    <div className="min-h-screen px-6 py-12">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs font-semibold px-4 py-2 rounded-full mb-4 uppercase tracking-wide">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Synthesis Complete
          </div>
          <h2 className="text-3xl font-bold text-slate-100 mb-2">Review Your Slides</h2>
          <p className="text-slate-400 text-sm">
            Edit any slide before generating the final presentation.
          </p>
        </div>

        {/* Stats bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          <StatsBadge icon={Presentation} label="Total Slides" value={totalSlides} color="text-blue-400" />
          <StatsBadge icon={BarChart2} label="Results" value={resultSlides} color="text-emerald-400" />
          <StatsBadge icon={FileText} label="Methodology" value={methodSlides} color="text-purple-400" />
          <StatsBadge icon={Image} label="With Images" value={withImages} color="text-orange-400" />
        </div>

        {/* Slide list */}
        <div className="space-y-3 mb-8">
          {slides.map((slide, idx) => (
            <div key={`${slide.order}-${idx}`} className="animate-slide-up" style={{ animationDelay: `${idx * 30}ms` }}>
              <SlideCard
                slide={slide}
                index={idx}
                onChange={(updated) => updateSlide(idx, updated)}
              />
            </div>
          ))}
        </div>

        {/* Optional feedback */}
        <div className="card-base mb-6">
          <label className="flex items-center gap-2 text-sm text-slate-300 font-medium mb-2">
            <MessageSquare className="w-4 h-4 text-slate-500" />
            Additional Instructions (optional)
          </label>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            className="input-base min-h-[80px] resize-y text-sm"
            placeholder="e.g. 'Make it more technical', 'Add more detail on methodology', 'Shorten all slides'…"
          />
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-start gap-3 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl px-4 py-3 text-sm mb-6">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            {error}
          </div>
        )}

        {/* Generate button */}
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="btn-primary w-full flex items-center justify-center gap-3 text-base py-4"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Generating presentation…
            </>
          ) : (
            <>
              <Presentation className="w-5 h-5" />
              Generate Presentation
              <CheckCircle2 className="w-5 h-5" />
            </>
          )}
        </button>

        <p className="text-center text-xs text-slate-600 mt-3">
          This will generate PPTX, DOCX, and PDF versions of your presentation.
        </p>
      </div>
    </div>
  );
}

