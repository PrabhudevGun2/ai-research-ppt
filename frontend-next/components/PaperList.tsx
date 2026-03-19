'use client';

import { useState } from 'react';
import { BookOpen, Users, Calendar, Tag, ExternalLink, ChevronDown, ChevronUp, CheckCircle2, Loader2, Search } from 'lucide-react';
import type { DiscoveredPaper } from '@/lib/types';
import { resumeSession } from '@/lib/api';

function formatDate(d: string) {
  try { return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }); }
  catch { return d; }
}

function formatAuthors(a: string[]) {
  return a.length <= 3 ? a.join(', ') : `${a.slice(0, 3).join(', ')} +${a.length - 3} more`;
}

function getCategoryColor(cat: string) {
  const map: Record<string, string> = {
    'cs.AI':  'bg-violet-50 text-violet-700 border-violet-200',
    'cs.LG':  'bg-blue-50 text-blue-700 border-blue-200',
    'cs.CL':  'bg-cyan-50 text-cyan-700 border-cyan-200',
    'cs.CV':  'bg-emerald-50 text-emerald-700 border-emerald-200',
    'cs.NE':  'bg-orange-50 text-orange-700 border-orange-200',
    'stat.ML':'bg-amber-50 text-amber-700 border-amber-200',
  };
  return map[cat] || 'bg-gray-50 text-gray-600 border-gray-200';
}

function PaperCard({ paper, index, onSelect, isSelecting, isSelected }: {
  paper: DiscoveredPaper; index: number;
  onSelect: (p: DiscoveredPaper) => void;
  isSelecting: boolean; isSelected: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className={`bg-white border-2 rounded-2xl overflow-hidden transition-all duration-200 hover:shadow-md ${
      isSelected ? 'border-blue-400 shadow-md' : 'border-gray-100 hover:border-gray-200'
    }`}>
      <div className="p-5">
        <div className="flex items-start justify-between gap-3 mb-3">
          <span className="shrink-0 flex items-center justify-center w-7 h-7 rounded-lg bg-blue-50 border border-blue-100 text-blue-700 text-xs font-bold">
            {index + 1}
          </span>
          <div className="flex flex-wrap gap-1.5 flex-1 justify-end">
            {paper.categories.slice(0, 3).map((cat) => (
              <span key={cat} className={`text-xs px-2 py-0.5 rounded-full border font-medium ${getCategoryColor(cat)}`}>{cat}</span>
            ))}
          </div>
        </div>
        <h3 className="text-gray-900 font-semibold text-sm leading-snug mb-3 line-clamp-3">{paper.title}</h3>
        <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-xs text-gray-400 mb-4">
          <span className="flex items-center gap-1.5"><Users className="w-3.5 h-3.5" />{formatAuthors(paper.authors)}</span>
          <span className="flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5" />{formatDate(paper.published)}</span>
          <span className="flex items-center gap-1.5"><Tag className="w-3.5 h-3.5" />{paper.arxiv_id}</span>
        </div>
        <button onClick={() => setExpanded(e => !e)} className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-blue-600 transition-colors">
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          {expanded ? 'Hide' : 'Show'} abstract
        </button>
        {expanded && (
          <div className="mt-3 text-xs text-gray-500 leading-relaxed bg-gray-50 rounded-xl p-3 border border-gray-100 animate-fade-in">
            {paper.summary}
          </div>
        )}
      </div>
      <div className="border-t border-gray-100 px-5 py-3 flex items-center justify-between bg-gray-50/50">
        <a href={paper.url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
          className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-blue-600 transition-colors">
          <ExternalLink className="w-3.5 h-3.5" /> View on ArXiv
        </a>
        <button onClick={() => onSelect(paper)} disabled={isSelecting}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
            isSelected ? 'bg-emerald-600 text-white'
            : 'bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed'
          }`}>
          {isSelecting && isSelected ? <><Loader2 className="w-4 h-4 animate-spin" /> Selecting…</>
            : isSelected ? <><CheckCircle2 className="w-4 h-4" /> Selected</>
            : 'Select Paper'}
        </button>
      </div>
    </div>
  );
}

export default function PaperList({ papers, sessionId }: { papers: DiscoveredPaper[]; sessionId: string }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');

  const filtered = query.trim()
    ? papers.filter(p => p.title.toLowerCase().includes(query.toLowerCase()) || p.authors.some(a => a.toLowerCase().includes(query.toLowerCase())))
    : papers;

  const handleSelect = async (paper: DiscoveredPaper) => {
    setSelectedId(paper.arxiv_id);
    setIsSelecting(true);
    setError('');
    try {
      await resumeSession(sessionId, { action: 'select_paper', selected_paper: paper });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to select paper');
      setSelectedId(null);
      setIsSelecting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-12">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-100 text-blue-700 text-xs font-semibold px-4 py-2 rounded-full mb-4">
            <BookOpen className="w-3.5 h-3.5" /> Paper Selection
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">{papers.length} Papers Found</h2>
          <p className="text-gray-500 text-sm">Select the paper you want to convert into a presentation.</p>
        </div>

        {papers.length > 3 && (
          <div className="relative mb-5">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input type="text" value={query} onChange={e => setQuery(e.target.value)}
              placeholder="Filter by title or author…" className="input-base pl-10" />
          </div>
        )}

        {error && <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm mb-5">{error}</div>}

        {filtered.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            <Search className="w-8 h-8 mx-auto mb-3 opacity-30" />
            <p>No papers match your filter.</p>
          </div>
        )}

        <div className="space-y-4">
          {filtered.map((paper, idx) => (
            <PaperCard key={paper.arxiv_id} paper={paper} index={papers.indexOf(paper)}
              onSelect={handleSelect} isSelecting={isSelecting} isSelected={selectedId === paper.arxiv_id} />
          ))}
        </div>
      </div>
    </div>
  );
}
