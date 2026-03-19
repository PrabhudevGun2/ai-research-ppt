'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  Key,
  Link2,
  Search,
  Users,
  Cpu,
  Sparkles,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  Loader2,
  BookOpen,
  Brain,
  Zap,
  FileText,
  Presentation,
  ArrowRight,
  GraduationCap,
  Briefcase,
  FlaskConical,
  Code2,
} from 'lucide-react';
import { createSession } from '@/lib/api';
import type { AudienceType, ModelOption } from '@/lib/types';

// ─── Constants ────────────────────────────────────────────────────────────────

const TOPIC_CHIPS = [
  'Transformer Attention',
  'Diffusion Models',
  'Large Language Models',
  'Reinforcement Learning',
  'Graph Neural Networks',
  'Vision Transformers',
  'Multimodal AI',
  'AI Safety',
];

const AUDIENCE_OPTIONS = [
  {
    value: 'executive' as AudienceType,
    label: 'Executive / Manager',
    description: 'High-level insights, business impact, minimal jargon',
    Icon: Briefcase,
  },
  {
    value: 'student' as AudienceType,
    label: 'Student / Fresher',
    description: 'Clear explanations, fundamentals first, learning-focused',
    Icon: GraduationCap,
  },
  {
    value: 'engineer' as AudienceType,
    label: 'AI Engineer',
    description: 'Technical depth, implementation details, code concepts',
    Icon: Code2,
  },
  {
    value: 'researcher' as AudienceType,
    label: 'Researcher',
    description: 'Full academic depth, methodology, citations, novelty',
    Icon: FlaskConical,
  },
];

const MODELS: ModelOption[] = [
  { value: 'google/gemini-2.0-flash-001', label: 'Gemini 2.0 Flash', provider: 'Google' },
  { value: 'google/gemini-2.5-pro-preview', label: 'Gemini 2.5 Pro Preview', provider: 'Google' },
  { value: 'anthropic/claude-3.5-sonnet', label: 'Claude 3.5 Sonnet', provider: 'Anthropic' },
  { value: 'anthropic/claude-3.5-haiku', label: 'Claude 3.5 Haiku', provider: 'Anthropic' },
  { value: 'openai/gpt-4o', label: 'GPT-4o', provider: 'OpenAI' },
  { value: 'openai/gpt-4o-mini', label: 'GPT-4o Mini', provider: 'OpenAI' },
  { value: 'meta-llama/llama-3.1-70b-instruct', label: 'Llama 3.1 70B', provider: 'Meta' },
  { value: 'mistralai/mistral-large', label: 'Mistral Large', provider: 'Mistral' },
];

const HOW_IT_WORKS = [
  {
    Icon: Search,
    title: 'Discover Papers',
    description:
      'Paste an ArXiv URL directly or search by topic. The AI fetches and ranks the most relevant papers.',
  },
  {
    Icon: Brain,
    title: 'Deep Synthesis',
    description:
      'The AI reads the full paper, extracts key concepts, methodology, results, and creates structured slide content.',
  },
  {
    Icon: FileText,
    title: 'Review & Edit',
    description:
      'Inspect every slide before generating. Edit titles and bullet points to match your exact needs.',
  },
  {
    Icon: Presentation,
    title: 'Download',
    description:
      'Get your presentation as PPTX, DOCX, and PDF — ready for any platform.',
  },
];

// ─── Validation ───────────────────────────────────────────────────────────────

function isValidArxivUrl(url: string): boolean {
  return /arxiv\.org\/(abs|pdf)\/[\d.]+/.test(url);
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function StepLabel({ number, label }: { number: number; label: string }) {
  return (
    <div className="flex items-center gap-3 mb-3">
      <div className="flex items-center justify-center w-7 h-7 rounded-full bg-blue-600/20 border border-blue-500/40 text-blue-400 text-sm font-bold shrink-0">
        {number}
      </div>
      <span className="text-slate-300 font-medium text-sm uppercase tracking-wider">
        {label}
      </span>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function HomePage() {
  const router = useRouter();

  // Form state
  const [apiKey, setApiKey] = useState('');
  const [arxivUrl, setArxivUrl] = useState('');
  const [topicQuery, setTopicQuery] = useState('');
  const [audience, setAudience] = useState<AudienceType>('researcher');
  const [model, setModel] = useState(MODELS[0].value);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [accordionOpen, setAccordionOpen] = useState(false);

  const arxivValid = isValidArxivUrl(arxivUrl);
  const canSubmit =
    !isLoading &&
    apiKey.trim().length > 0 &&
    (arxivValid || topicQuery.trim().length > 2);

  const handleTopicChip = useCallback(
    (topic: string) => {
      setTopicQuery(topic);
      setArxivUrl('');
    },
    []
  );

  const handleArxivChange = (val: string) => {
    setArxivUrl(val);
    if (val.trim()) setTopicQuery('');
  };

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setIsLoading(true);
    setError('');
    try {
      const payload: Record<string, string> = {
        api_key: apiKey.trim(),
        model,
        audience,
      };
      if (arxivValid && arxivUrl.trim()) {
        payload.arxiv_url = arxivUrl.trim();
      } else {
        payload.user_query = topicQuery.trim();
      }
      const data = await createSession(payload);
      router.push(`/session/${data.session_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create session. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      {/* ── Hero ─────────────────────────────────────────────────── */}
      <section
        className="relative overflow-hidden"
        style={{
          background:
            'linear-gradient(160deg, #0b1120 0%, #0c1a3a 45%, #0b1120 100%)',
        }}
      >
        {/* Decorative orbs */}
        <div
          className="absolute top-[-80px] right-[-80px] w-[500px] h-[500px] rounded-full opacity-10 pointer-events-none"
          style={{
            background:
              'radial-gradient(circle, rgba(99,102,241,0.6) 0%, transparent 70%)',
            filter: 'blur(60px)',
          }}
        />
        <div
          className="absolute bottom-[-100px] left-[-60px] w-[400px] h-[400px] rounded-full opacity-8 pointer-events-none"
          style={{
            background:
              'radial-gradient(circle, rgba(59,130,246,0.5) 0%, transparent 70%)',
            filter: 'blur(60px)',
          }}
        />

        <div className="relative max-w-4xl mx-auto px-6 pt-20 pb-16 text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/25 text-blue-400 text-xs font-semibold px-4 py-2 rounded-full mb-6 tracking-wide uppercase">
            <Sparkles className="w-3.5 h-3.5" />
            Powered by OpenRouter AI Models
          </div>

          <h1 className="text-5xl sm:text-6xl font-extrabold leading-tight mb-5">
            <span className="text-gradient">AI Research</span>
            <br />
            <span className="text-white">PPT Generator</span>
          </h1>

          <p className="text-slate-400 text-lg sm:text-xl max-w-2xl mx-auto leading-relaxed mb-8">
            Transform any ArXiv paper or research topic into a beautifully structured
            PowerPoint presentation — in minutes, not hours.
          </p>

          {/* Quick feature pills */}
          <div className="flex flex-wrap justify-center gap-3 text-sm text-slate-400">
            {[
              { Icon: Zap, text: 'Auto-synthesizes paper content' },
              { Icon: BookOpen, text: 'ArXiv URL or topic search' },
              { Icon: FileText, text: 'PPTX · DOCX · PDF export' },
            ].map(({ Icon, text }) => (
              <div
                key={text}
                className="flex items-center gap-1.5 bg-slate-800/60 border border-slate-700/60 rounded-full px-3 py-1.5"
              >
                <Icon className="w-3.5 h-3.5 text-blue-400" />
                {text}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Form ─────────────────────────────────────────────────── */}
      <section className="max-w-2xl mx-auto px-6 py-10 space-y-6">
        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl px-4 py-3 text-sm animate-fade-in">
            {error}
          </div>
        )}

        {/* Step 1: API Key */}
        <div className="card-base animate-slide-up">
          <StepLabel number={1} label="OpenRouter API Key" />
          <div className="relative">
            <Key className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-or-v1-..."
              className={`input-base pl-10 pr-10 transition-all ${
                apiKey.trim() ? 'border-green-500/60 ring-1 ring-green-500/20' : ''
              }`}
            />
            {apiKey.trim() && (
              <CheckCircle2 className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-green-500 animate-fade-in" />
            )}
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Get your free key at{' '}
            <a
              href="https://openrouter.ai/keys"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 underline underline-offset-2"
            >
              openrouter.ai/keys
            </a>
            . Your key is never stored.
          </p>
        </div>

        {/* Step 2: ArXiv URL */}
        <div className="card-base animate-slide-up">
          <StepLabel number={2} label="ArXiv Paper URL" />
          <div className="relative">
            <Link2 className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="url"
              value={arxivUrl}
              onChange={(e) => handleArxivChange(e.target.value)}
              placeholder="https://arxiv.org/abs/2401.12345"
              className={`input-base pl-10 pr-10 ${
                arxivUrl && !arxivValid
                  ? 'border-red-500/50 ring-1 ring-red-500/20'
                  : arxivValid
                  ? 'border-green-500/60 ring-1 ring-green-500/20'
                  : ''
              }`}
            />
            {arxivValid && (
              <CheckCircle2 className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-green-500" />
            )}
            {arxivUrl && !arxivValid && (
              <span className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-red-400 text-xs font-bold">
                !
              </span>
            )}
          </div>
          {arxivUrl && !arxivValid && (
            <p className="text-xs text-red-400 mt-1.5">
              Please enter a valid ArXiv URL (e.g. arxiv.org/abs/2401.12345)
            </p>
          )}
        </div>

        {/* OR Divider */}
        <div className="flex items-center gap-4">
          <div className="flex-1 h-px bg-slate-700" />
          <span className="text-slate-500 text-xs font-semibold uppercase tracking-widest px-1">
            or
          </span>
          <div className="flex-1 h-px bg-slate-700" />
        </div>

        {/* Step 3: Topic Search */}
        <div className="card-base animate-slide-up">
          <StepLabel number={3} label="Search by Topic" />
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              value={topicQuery}
              onChange={(e) => {
                setTopicQuery(e.target.value);
                if (e.target.value.trim()) setArxivUrl('');
              }}
              placeholder="e.g. attention mechanisms in transformers"
              className={`input-base pl-10 ${
                topicQuery.trim().length > 2 ? 'border-blue-500/50 ring-1 ring-blue-500/20' : ''
              }`}
            />
          </div>

          {/* Topic chips */}
          <div className="flex flex-wrap gap-2 mt-3">
            {TOPIC_CHIPS.map((topic) => (
              <button
                key={topic}
                onClick={() => handleTopicChip(topic)}
                className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-all duration-150 ${
                  topicQuery === topic
                    ? 'bg-blue-600 border-blue-500 text-white shadow-blue-glow'
                    : 'bg-slate-700/60 border-slate-600 text-slate-300 hover:border-blue-500/50 hover:text-blue-300'
                }`}
              >
                {topic}
              </button>
            ))}
          </div>
        </div>

        {/* Step 4: Audience */}
        <div className="card-base animate-slide-up">
          <StepLabel number={4} label="Target Audience" />
          <div className="grid grid-cols-2 gap-3">
            {AUDIENCE_OPTIONS.map(({ value, label, description, Icon }) => (
              <button
                key={value}
                onClick={() => setAudience(value)}
                className={`relative flex flex-col items-start gap-2 p-4 rounded-xl border text-left transition-all duration-200 ${
                  audience === value
                    ? 'bg-blue-600/15 border-blue-500/60 shadow-blue-glow'
                    : 'bg-slate-700/40 border-slate-600/60 hover:border-slate-500'
                }`}
              >
                {audience === value && (
                  <div className="absolute top-2 right-2">
                    <CheckCircle2 className="w-4 h-4 text-blue-400" />
                  </div>
                )}
                <div
                  className={`p-2 rounded-lg ${
                    audience === value ? 'bg-blue-500/20' : 'bg-slate-600/40'
                  }`}
                >
                  <Icon
                    className={`w-4 h-4 ${
                      audience === value ? 'text-blue-400' : 'text-slate-400'
                    }`}
                  />
                </div>
                <div>
                  <div
                    className={`text-sm font-semibold ${
                      audience === value ? 'text-blue-300' : 'text-slate-200'
                    }`}
                  >
                    {label}
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5 leading-snug">
                    {description}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Step 5: Model */}
        <div className="card-base animate-slide-up">
          <StepLabel number={5} label="AI Model" />
          <div className="relative">
            <Cpu className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
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
            <ChevronDown className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
          </div>
        </div>

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="btn-primary w-full flex items-center justify-center gap-3 text-base py-4"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Creating session…
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              Generate Presentation
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </button>

        {!canSubmit && !isLoading && (
          <p className="text-center text-xs text-slate-600">
            {!apiKey.trim()
              ? 'Enter your OpenRouter API key to continue'
              : 'Enter an ArXiv URL or topic query to continue'}
          </p>
        )}
      </section>

      {/* ── How it Works ─────────────────────────────────────────── */}
      <section className="max-w-2xl mx-auto px-6 pb-16">
        <div className="card-base">
          <button
            className="w-full flex items-center justify-between text-left"
            onClick={() => setAccordionOpen((o) => !o)}
            aria-expanded={accordionOpen}
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <BookOpen className="w-5 h-5 text-purple-400" />
              </div>
              <span className="text-slate-200 font-semibold">How it works</span>
            </div>
            <ChevronDown
              className={`w-5 h-5 text-slate-400 transition-transform duration-200 ${
                accordionOpen ? 'rotate-180' : ''
              }`}
            />
          </button>

          {accordionOpen && (
            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4 animate-fade-in">
              {HOW_IT_WORKS.map(({ Icon, title, description }, idx) => (
                <div
                  key={title}
                  className="flex gap-4 p-4 bg-slate-700/30 rounded-xl border border-slate-700/50"
                >
                  <div className="shrink-0 flex items-center justify-center w-9 h-9 rounded-lg bg-blue-500/10 text-blue-400 font-bold text-sm border border-blue-500/20">
                    {idx + 1}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className="w-4 h-4 text-blue-400" />
                      <span className="text-slate-200 font-medium text-sm">{title}</span>
                    </div>
                    <p className="text-slate-500 text-xs leading-relaxed">{description}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────── */}
      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-600">
        <p>
          Built with Next.js · Powered by{' '}
          <a
            href="https://openrouter.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-500 hover:text-slate-400 underline underline-offset-2"
          >
            OpenRouter
          </a>{' '}
          · Papers from{' '}
          <a
            href="https://arxiv.org"
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-500 hover:text-slate-400 underline underline-offset-2"
          >
            ArXiv
          </a>
        </p>
      </footer>
    </div>
  );
}
