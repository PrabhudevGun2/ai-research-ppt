// ─── Paper Discovery ────────────────────────────────────────────────────────

export interface DiscoveredPaper {
  arxiv_id: string;
  title: string;
  authors: string[];
  summary: string;
  published: string;
  url: string;
  pdf_url: string;
  categories: string[];
}

// ─── Slide Content ──────────────────────────────────────────────────────────

export type SlideType =
  | 'title'
  | 'problem'
  | 'motivation'
  | 'background'
  | 'methodology'
  | 'results'
  | 'conclusion'
  | 'future_work'
  | 'references'
  | 'generic';

export interface SlideContent {
  slide_type: SlideType;
  topic?: string;
  title: string;
  subtitle?: string;
  body_points: string[];
  speaker_notes?: string;
  order: number;
  image_path?: string;
  image_caption?: string;
}

// ─── Generated PPT ──────────────────────────────────────────────────────────

export interface GeneratedPPT {
  file_path: string;
  doc_path?: string;
  pdf_path?: string;
  session_id: string;
  slide_count: number;
  topics_covered: string[];
  generated_at: string;
}

// ─── Session / API ──────────────────────────────────────────────────────────

export type SessionStage =
  | 'discovering_papers'
  | 'awaiting_paper_selection'
  | 'processing_paper'
  | 'synthesizing'
  | 'awaiting_synthesis_review'
  | 'generating_ppt'
  | 'awaiting_final_review'
  | 'completed'
  | 'resuming'
  | 'failed';

export interface InterruptPayload {
  papers?: DiscoveredPaper[];
  slides?: SlideContent[];
  generated_ppt?: GeneratedPPT;
  message?: string;
}

export interface SessionStatus {
  session_id: string;
  stage: SessionStage;
  interrupt_payload?: InterruptPayload;
  error?: string;
}

export interface CreateSessionRequest {
  user_query?: string;
  arxiv_url?: string;
  model?: string;
  api_key?: string;
  audience?: string;
}

export interface CreateSessionResponse {
  session_id: string;
  status: string;
}

export interface ResumeRequest {
  action: string;
  feedback_text?: string;
  selected_paper?: DiscoveredPaper;
  approved_slides?: SlideContent[];
  timestamp?: string;
}

// ─── UI ─────────────────────────────────────────────────────────────────────

export type AudienceType = 'executive' | 'student' | 'engineer' | 'researcher';

export interface AudienceOption {
  value: AudienceType;
  label: string;
  description: string;
  icon: string;
}

export type ModelOption = {
  value: string;
  label: string;
  provider: string;
};
