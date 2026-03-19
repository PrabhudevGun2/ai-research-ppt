import type {
  CreateSessionRequest,
  CreateSessionResponse,
  SessionStatus,
  ResumeRequest,
} from './types';

const BASE_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, '') ||
  'http://localhost:8000';

const API_BASE = `${BASE_URL}/api/v1`;

// ─── Helpers ─────────────────────────────────────────────────────────────────

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const body = await res.json();
      message = body.detail || body.message || message;
    } catch {
      // ignore parse errors
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

// ─── API Functions ────────────────────────────────────────────────────────────

/**
 * Create a new session with initial parameters.
 */
export async function createSession(
  payload: CreateSessionRequest
): Promise<CreateSessionResponse> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse<CreateSessionResponse>(res);
}

/**
 * Poll the current status/stage of a session.
 */
export async function getSessionStatus(sessionId: string): Promise<SessionStatus> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/status`, {
    cache: 'no-store',
  });
  return handleResponse<SessionStatus>(res);
}

/**
 * Resume a paused session with user action/feedback.
 */
export async function resumeSession(
  sessionId: string,
  payload: ResumeRequest
): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/resume`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...payload,
      timestamp: payload.timestamp || new Date().toISOString(),
    }),
  });
  return handleResponse<{ status: string }>(res);
}

/**
 * Download the generated PPTX file as a Blob.
 */
export async function downloadPPT(sessionId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/ppt/download`);
  if (!res.ok) throw new Error(`Failed to download PPTX: ${res.statusText}`);
  return res.blob();
}

/**
 * Download the generated DOCX file as a Blob.
 */
export async function downloadDOCX(sessionId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/doc/download`);
  if (!res.ok) throw new Error(`Failed to download DOCX: ${res.statusText}`);
  return res.blob();
}

/**
 * Download the generated PDF file as a Blob.
 */
export async function downloadPDF(sessionId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/pdf/download`);
  if (!res.ok) throw new Error(`Failed to download PDF: ${res.statusText}`);
  return res.blob();
}

/**
 * Check backend health.
 */
export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/health`, { cache: 'no-store' });
  return handleResponse<{ status: string }>(res);
}

/**
 * Trigger a browser download from a Blob.
 */
export function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
