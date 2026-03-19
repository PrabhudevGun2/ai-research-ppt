'use client';

import { useState } from 'react';
import {
  BookOpen,
  Users,
  Calendar,
  Tag,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Loader2,
  Search,
} from 'lucide-react';
import type { DiscoveredPaper } from '@/lib/types';
import { resumeSession } from '@/lib/api';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

function formatAuthors(authors: string[]): string {
  if (authors.length <= 3) return authors.join(', ');
  return `${authors.slice(0, 3).join(', ')} +${authors.length - 3} more`;
}

// Category color mapping
function getCategoryColor(cat: string): string {
  const colors: Record<string, string> = {
    'cs.AI': 'bg-purple-500/15 text-purple-400 border-purple-500/25',
    'cs.LG': 'bg-blue-500/15 text-blue-400 border-blue-500/25',
    'cs.CL': 'bg-cyan-500/15 text-cyan-400 border-cyan-500/25',
    'cs.CV': 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25',
    'cs.NE': 'bg-orange-500/15 text-orange-400 border-orange-500/25',
    'stat.ML': 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25',
  };
  return colors[cat] || 'bg-slate-700/40 text-slate-400 border-slate-600/40';
}

// ─── Paper Card ───────────────────────────────────────────────────────────────

interface PaperCardProps {
  paper: DiscoveredPaper;
  index: number;
  onSelect: (paper: DiscoveredPaper) => void;
  isSelecting: boolean;
  isSelected: boolean;
}

function PaperCard({ paper, index, onSelect, isSelecting, isSelected }: PaperCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`bg-slate-800 border rounded-2xl overflow-hidden transition-all duration-300 card-hover ${
        isSelected
          ? 'border-blue-500/60 shadow-blue-glow'
          : 'border-slate-700 hover:border-slate-600'
      }`}
    >
      {/* Header */}
      <div className="p-5">
        {/* Index + categories */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <span className="shrink-0 flex items-center justify-center w-7 h-7 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-bold">
            {index + 1}
          </span>
          <div className="flex flex-wrap gap-1.5 flex-1 justify-end">
            {paper.categories.slice(0, 3).map((cat) => (
              <span
                key={cat}
                className={`text-xs px-2 py-0.5 rounded-full border font-medium ${getCategoryColor(cat)}`}
              >
                {cat}
              </span>
            ))}
          </div>
        </div>

        {/* Title */}
        <h3 className="text-slate-100 font-semibold text-sm leading-snug mb-3 line-clamp-3">
          {paper.title}
        </h3>

        {/* Meta */}
        <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-xs text-slate-500 mb-4">
          <span className="flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-slate-600" />
            {formatAuthors(paper.authors)}
          </span>
          <span className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-slate-600" />
            {formatDate(paper.published)}
          </span>
          <span className="flex items-center gap-1.5">
            <Tag className="w-3.5 h-3.5 text-slate-600" />
            {paper.arxiv_id}
          </span>
        </div>

        {/* Abstract toggle */}
        <button
          onClick={() => setExpanded((e) => !e)}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-300 transition-colors"
        >
          {expanded ? (
            <ChevronUp className="w-3.5 h-3.5" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5" />
          )}
          {expanded ? 'Hide' : 'Show'} abstract
        </button>

        {/* Abstract */}
        {expanded && (
          <div className="mt-3 text-xs text-slate-400 leading-relaxed bg-slate-700/30 rounded-xl p-3 border border-slate-700/50 animate-fade-in">
            {paper.summary}
          </div>
        )}
      </div>

      {/* Footer actions */}
      <div className="border-t border-slate-700/60 px-5 py-3 flex items-center justify-between bg-slate-800/50">
        <a
          href={paper.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-blue-400 transition-colors"
          onClick={(e) => e.stopPropagation()}
        >
          <ExternalLink className="w-3.5 h-3.5" />
          View on ArXiv
        </a>

        <button
          onClick={() => onSelect(paper)}
          disabled={isSelecting}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
            isSelected
              ? 'bg-emerald-600 text-white border border-emerald-500'
              : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-glow disabled:opacity-50 disabled:cursor-not-allowed'
          }`}
        >
          {isSelecting && isSelected ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Selecting…
            </>
          ) : isSelected ? (
            <>
              <CheckCircle2 className="w-4 h-4" />
              Selected
            </>
          ) : (
            'Select Paper'
          )}
        </button>
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

interface PaperListProps {
  papers: DiscoveredPaper[];
  sessionId: string;
}

export default function PaperList({ papers, sessionId }: PaperListProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = searchQuery.trim()
    ? papers.filter(
        (p) =>
          p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          p.authors.some((a) => a.toLowerCase().includes(searchQuery.toLowerCase())) ||
          p.summary.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : papers;

  const handleSelect = async (paper: DiscoveredPaper) => {
    setSelectedId(paper.arxiv_id);
    setIsSelecting(true);
    setError('');
    try {
      await resumeSession(sessionId, {
        action: 'select_paper',
        selected_paper: paper,
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to select paper');
      setSelectedId(null);
      setIsSelecting(false);
    }
  };

  return (
    <div className="min-h-screen px-6 py-12">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10 animate-fade-in">
          <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/25 text-blue-400 text-xs font-semibold px-4 py-2 rounded-full mb-4 uppercase tracking-wide">
            <BookOpen className="w-3.5 h-3.5" />
            Paper Selection
          </div>
          <h2 className="text-3xl font-bold text-slate-100 mb-2">
            {papers.length} Papers Found
          </h2>
          <p className="text-slate-400 text-sm">
            Select the paper you want to convert into a presentation.
          </p>
        </div>

        {/* Search */}
        {papers.length > 3 && (
          <div className="relative mb-6">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter papers by title, author, or keyword…"
              className="input-base pl-10"
            />
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl px-4 py-3 text-sm mb-6">
            {error}
          </div>
        )}

        {/* No results */}
        {filtered.length === 0 && (
          <div className="text-center py-12 text-slate-500">
            <Search className="w-8 h-8 mx-auto mb-3 opacity-40" />
            <p>No papers match your filter.</p>
          </div>
        )}

        {/* Paper grid */}
        <div className="space-y-4">
          {filtered.map((paper, idx) => (
            <div key={paper.arxiv_id} className="animate-slide-up" style={{ animationDelay: `${idx * 60}ms` }}>
              <PaperCard
                paper={paper}
                index={papers.indexOf(paper)}
                onSelect={handleSelect}
                isSelecting={isSelecting}
                isSelected={selectedId === paper.arxiv_id}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
