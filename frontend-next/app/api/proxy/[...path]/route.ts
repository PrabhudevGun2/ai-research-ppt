import { NextRequest, NextResponse } from 'next/server';

const BACKEND = (process.env.BACKEND_URL || 'http://localhost:8000').replace(/\/$/, '');

async function proxy(req: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path.join('/');
  const search = req.nextUrl.search;
  const url = `${BACKEND}/api/v1/${path}${search}`;

  const headers = new Headers();
  headers.set('Content-Type', req.headers.get('Content-Type') || 'application/json');

  const init: RequestInit = { method: req.method, headers };
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    init.body = await req.arrayBuffer();
  }

  try {
    const res = await fetch(url, init);
    const body = await res.arrayBuffer();
    const resHeaders = new Headers();
    res.headers.forEach((v, k) => {
      if (!['transfer-encoding', 'connection'].includes(k.toLowerCase())) {
        resHeaders.set(k, v);
      }
    });
    return new NextResponse(body, { status: res.status, headers: resHeaders });
  } catch (err) {
    return NextResponse.json({ detail: 'Backend unreachable' }, { status: 502 });
  }
}

export const GET     = proxy;
export const POST    = proxy;
export const PUT     = proxy;
export const DELETE  = proxy;
export const OPTIONS = proxy;
