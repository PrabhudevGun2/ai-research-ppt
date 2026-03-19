'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  Key, Link2, Search, Cpu, Sparkles, ChevronDown, CheckCircle2,
  Loader2, BookOpen, Brain, FileText, Presentation, ArrowRight,
  GraduationCap, Briefcase, FlaskConical, Code2, Zap, Lock,
} from 'lucide-react';
import { createSession } from '@/lib/api';
import type { AudienceType, ModelOption } from '@/lib/types';

const TOPIC_CHIPS = [
  'Transformer Attention', 'Diffusion Models', 'Large Language Models',
  'Reinforcement Learning', 'Graph Neural Networks', 'Vision Transformers',
  'Multimodal AI', 'AI Safety',
];

const AUDIENCE_OPTIONS = [
  { value: 'executive' as AudienceType, label: 'Executive', sub: 'Manager / Leader', description: 'Big-picture impact, no jargon', Icon: Briefcase, color: 'violet' },
  { value: 'fresher' as AudienceType, label: 'Student', sub: 'Fresher / Learner', description: 'Clear fundamentals, step-by-step', Icon: GraduationCap, color: 'emerald' },
  { value: 'engineer' as AudienceType, label: 'Engineer', sub: 'AI / ML Engineer', description: 'Technical depth, code concepts', Icon: Code2, color: 'blue' },
  { value: 'researcher' as AudienceType, label: 'Researcher', sub: 'Academic / Scientist', description: 'Full depth, equations, citations', Icon: FlaskConical, color: 'amber' },
];

const AUDIENCE_COLORS: Record<string, string> = {
  violet: 'border-violet-300 bg-violet-50 ring-violet-400',
  emerald: 'border-emerald-300 bg-emerald-50 ring-emerald-400',
  blue:    'border-blue-300 bg-blue-50 ring-blue-500',
  amber:   'border-amber-300 bg-amber-50 ring-amber-400',
};

const AUDIENCE_ICON_COLORS: Record<string, string> = {
  violet: 'text-violet-600 bg-violet-100',
  emerald: 'text-emerald-600 bg-emerald-100',
  blue:    'text-blue-600 bg-blue-100',
  amber:   'text-amber-600 bg-amber-100',
};

const MODELS: ModelOption[] = [
  { value: 'google/gemini-2.0-flash-001', label: 'Gemini 2.0 Flash', provider: 'Google' },
  { value: 'anthropic/claude-sonnet-4-5', label: 'Claude Sonnet 4.5', provider: 'Anthropic' },
  { value: 'anthropic/claude-3-haiku', label: 'Claude 3 Haiku (fast)', provider: 'Anthropic' },
  { value: 'openai/gpt-4o', label: 'GPT-4o', provider: 'OpenAI' },
  { value: 'openai/gpt-4o-mini', label: 'GPT-4o Mini (fast)', provider: 'OpenAI' },
  { value: 'google/gemini-pro-1.5', label: 'Gemini Pro 1.5', provider: 'Google' },
  { value: 'meta-llama/llama-3.1-70b-instruct', label: 'Llama 3.1 70B (free)', provider: 'Meta' },
  { value: 'deepseek/deepseek-chat', label: 'DeepSeek Chat V3', provider: 'DeepSeek' },
];

const HOW_IT_WORKS = [
  { Icon: Search,       title: 'Find Paper',    description: 'Paste an ArXiv URL or search by topic.' },
  { Icon: Brain,        title: 'AI Synthesis',  description: 'AI reads the full paper and structures slide content.' },
  { Icon: FileText,     title: 'Review & Edit', description: 'Preview every slide and refine before generating.' },
  { Icon: Presentation, title: 'Download',      description: 'Export as PPTX, Word doc, and PDF instantly.' },
];

function isValidArxivUrl(url: string): boolean {
  return /arxiv\.org\/(abs|pdf)\/[\d.]+/.test(url) || /^\d{4}\.\d{4,5}$/.test(url.trim());
}

function StepBadge({ n }: { n: number }) {
  return (
    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-600 text-white text-xs font-bold mr-2 shrink-0">
      {n}
    </span>
  );
}

export default function HomePage() {
  const router = useRouter();
  const [apiKey, setApiKey]       = useState('');
  const [arxivUrl, setArxivUrl]   = useState('');
  const [topicQuery, setTopicQuery] = useState('');
  const [audience, setAudience]   = useState<AudienceType>('engineer');
  const [model, setModel]         = useState(MODELS[0].value);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError]         = useState('');
  const [howOpen, setHowOpen]     = useState(false);

  const arxivValid = isValidArxivUrl(arxivUrl);
  const canSubmit  = !isLoading && apiKey.trim().length > 0 && (arxivValid || topicQuery.trim().length > 2);

  const handleTopicChip = useCallback((topic: string) => {
    setTopicQuery(topic);
    setArxivUrl('');
  }, []);

  const handleArxivChange = (val: string) => {
    setArxivUrl(val);
    if (val.trim()) setTopicQuery('');
  };

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setIsLoading(true);
    setError('');
    try {
      const payload: Record<string, string> = { api_key: apiKey.trim(), model, audience };
      if (arxivValid && arxivUrl.trim()) payload.arxiv_url = arxivUrl.trim();
      else payload.user_query = topicQuery.trim();
      const data = await createSession(payload);
      router.push(`/session/${data.session_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create session. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* ── Navbar ─────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur border-b border-gray-100 px-6 py-3">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
              <Presentation className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-gray-900 text-sm">ResearchPPT</span>
            <span className="hidden sm:inline text-xs text-gray-400 ml-1">AI Generator</span>
          </div>
          <a
            href="https://openrouter.ai/keys"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
          >
            Get API Key <ArrowRight className="w-3 h-3" />
          </a>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────────────── */}
      <section className="bg-white border-b border-gray-100">
        <div className="max-w-3xl mx-auto px-6 py-16 text-center">
          <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-100 text-blue-700 text-xs font-semibold px-4 py-2 rounded-full mb-6">
            <Sparkles className="w-3.5 h-3.5" />
            Powered by OpenRouter · Any AI Model
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 leading-tight mb-4">
            Turn any{' '}
            <span className="text-gradient">ArXiv paper</span>
            <br />into a presentation
          </h1>
          <p className="text-gray-500 text-lg max-w-xl mx-auto mb-8 leading-relaxed">
            Paste a paper link or search by topic. The AI reads, synthesizes, and builds
            professional slides — tailored to your audience.
          </p>
          <div className="flex flex-wrap justify-center gap-3 text-sm text-gray-500">
            {[
              { Icon: Zap,          text: '15+ slides generated' },
              { Icon: BookOpen,     text: 'ArXiv URL or topic search' },
              { Icon: FileText,     text: 'PPTX · DOCX · PDF export' },
            ].map(({ Icon, text }) => (
              <div key={text} className="flex items-center gap-1.5 bg-gray-50 border border-gray-200 rounded-full px-3 py-1.5">
                <Icon className="w-3.5 h-3.5 text-blue-500" />
                {text}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Form ───────────────────────────────────────────────── */}
      <section className="max-w-2xl mx-auto px-4 py-10 space-y-5">

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm animate-fade-in flex items-start gap-2">
            <span className="text-red-500 font-bold mt-0.5">!</span>
            {error}
          </div>
        )}

        {/* Step 1: API Key */}
        <div className="card-base">
          <label className="flex items-center text-sm font-semibold text-gray-700 mb-3">
            <StepBadge n={1} /> OpenRouter API Key
          </label>
          <div className="relative">
            <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-or-v1-..."
              className={`input-base pl-10 pr-10 ${apiKey.trim() ? 'border-green-400 ring-1 ring-green-300' : ''}`}
            />
            {apiKey.trim() && (
              <CheckCircle2 className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-green-500" />
            )}
          </div>
          <p className="text-xs text-gray-400 mt-2 flex items-center gap-1">
            <Lock className="w-3 h-3" />
            Never stored. Used only for this session. Free key at{' '}
            <a href="https://openrouter.ai/keys" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">openrouter.ai/keys</a>
          </p>
        </div>

        {/* Step 2: ArXiv URL */}
        <div className="card-base">
          <label className="flex items-center text-sm font-semibold text-gray-700 mb-3">
            <StepBadge n={2} /> ArXiv Paper URL
            <span className="ml-2 text-xs font-normal text-gray-400">(recommended)</span>
          </label>
          <div className="relative">
            <Link2 className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="url"
              value={arxivUrl}
              onChange={(e) => handleArxivChange(e.target.value)}
              placeholder="https://arxiv.org/abs/1706.03762"
              className={`input-base pl-10 pr-10 ${
                arxivUrl && !arxivValid ? 'border-red-400 ring-1 ring-red-300'
                : arxivValid           ? 'border-green-400 ring-1 ring-green-300'
                : ''}`}
            />
            {arxivValid && <CheckCircle2 className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-green-500" />}
          </div>
          {arxivUrl && !arxivValid && (
            <p className="text-xs text-red-500 mt-1.5">Enter a valid ArXiv URL — e.g. arxiv.org/abs/2401.12345</p>
          )}
        </div>

        {/* OR */}
        <div className="flex items-center gap-4">
          <div className="flex-1 h-px bg-gray-200" />
          <span className="text-xs text-gray-400 font-semibold uppercase tracking-widest">or</span>
          <div className="flex-1 h-px bg-gray-200" />
        </div>

        {/* Step 3: Topic Search */}
        <div className="card-base">
          <label className="flex items-center text-sm font-semibold text-gray-700 mb-3">
            <StepBadge n={3} /> Search by Topic
          </label>
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={topicQuery}
              onChange={(e) => { setTopicQuery(e.target.value); if (e.target.value.trim()) setArxivUrl(''); }}
              placeholder="e.g. attention mechanisms in transformers"
              className={`input-base pl-10 ${topicQuery.trim().length > 2 ? 'border-blue-400 ring-1 ring-blue-300' : ''}`}
            />
          </div>
          <div className="flex flex-wrap gap-2 mt-3">
            {TOPIC_CHIPS.map((topic) => (
              <button
                key={topic}
                onClick={() => handleTopicChip(topic)}
                className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-all ${
                  topicQuery === topic
                    ? 'bg-blue-600 border-blue-600 text-white shadow-sm'
                    : 'bg-white border-gray-200 text-gray-600 hover:border-blue-300 hover:text-blue-600'
                }`}
              >
                {topic}
              </button>
            ))}
          </div>
        </div>

        {/* Step 4: Audience */}
        <div className="card-base">
          <label className="flex items-center text-sm font-semibold text-gray-700 mb-3">
            <StepBadge n={4} /> Target Audience
          </label>
          <div className="grid grid-cols-2 gap-3">
            {AUDIENCE_OPTIONS.map(({ value, label, sub, description, Icon, color }) => {
              const isSelected = audience === value;
              const ringClass  = AUDIENCE_COLORS[color];
              const iconClass  = AUDIENCE_ICON_COLORS[color];
              return (
                <button
                  key={value}
                  onClick={() => setAudience(value)}
                  className={`relative flex flex-col items-start gap-2 p-4 rounded-xl border-2 text-left transition-all duration-150 ${
                    isSelected ? `${ringClass} ring-2 shadow-sm` : 'border-gray-100 bg-gray-50 hover:border-gray-200'
                  }`}
                >
                  {isSelected && (
                    <CheckCircle2 className="absolute top-2.5 right-2.5 w-4 h-4 text-blue-600" />
                  )}
                  <div className={`p-2 rounded-lg ${iconClass}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-gray-900">{label}</div>
                    <div className="text-xs text-gray-500">{sub}</div>
                    <div className="text-xs text-gray-400 mt-0.5">{description}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Step 5: Model */}
        <div className="card-base">
          <label className="flex items-center text-sm font-semibold text-gray-700 mb-3">
            <StepBadge n={5} /> AI Model
          </label>
          <div className="relative">
            <Cpu className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="input-base pl-10 appearance-none cursor-pointer"
            >
              {MODELS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label} — {m.provider}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="btn-primary w-full flex items-center justify-center gap-3 text-base py-4"
        >
          {isLoading ? (
            <><Loader2 className="w-5 h-5 animate-spin" /> Creating session…</>
          ) : (
            <><Sparkles className="w-5 h-5" /> Generate Presentation <ArrowRight className="w-5 h-5" /></>
          )}
        </button>

        {!canSubmit && !isLoading && (
          <p className="text-center text-xs text-gray-400">
            {!apiKey.trim() ? 'Enter your OpenRouter API key to continue'
              : 'Enter an ArXiv URL or a topic to continue'}
          </p>
        )}

        {/* How it works */}
        <div className="card-base">
          <button
            className="w-full flex items-center justify-between text-left"
            onClick={() => setHowOpen((o) => !o)}
          >
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-blue-500" />
              <span className="text-sm font-semibold text-gray-700">How it works</span>
            </div>
            <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${howOpen ? 'rotate-180' : ''}`} />
          </button>
          {howOpen && (
            <div className="mt-5 grid grid-cols-2 gap-3 animate-fade-in">
              {HOW_IT_WORKS.map(({ Icon, title, description }, idx) => (
                <div key={title} className="flex gap-3 p-3 bg-gray-50 rounded-xl border border-gray-100">
                  <div className="shrink-0 flex items-center justify-center w-8 h-8 rounded-lg bg-blue-50 text-blue-600 font-bold text-xs border border-blue-100">
                    {idx + 1}
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <Icon className="w-3.5 h-3.5 text-blue-500" />
                      <span className="text-gray-800 font-semibold text-xs">{title}</span>
                    </div>
                    <p className="text-gray-400 text-xs leading-relaxed">{description}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────── */}
      <footer className="border-t border-gray-100 bg-white py-6 text-center text-xs text-gray-400">
        Built with Next.js ·{' '}
        <a href="https://openrouter.ai" target="_blank" rel="noopener noreferrer" className="hover:text-gray-600 underline underline-offset-2">OpenRouter</a>
        {' '}· Papers from{' '}
        <a href="https://arxiv.org" target="_blank" rel="noopener noreferrer" className="hover:text-gray-600 underline underline-offset-2">ArXiv</a>
      </footer>
    </div>
  );
}
