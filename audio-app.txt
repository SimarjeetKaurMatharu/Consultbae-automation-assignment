SQL Code for Audio App

CREATE TABLE IF NOT EXISTS audio_submissions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  submitter_name text NOT NULL,
  phone text NOT NULL,
  storage_path text NOT NULL,
  file_name text NOT NULL,
  mime_type text NOT NULL,
  file_size bigint NOT NULL,
  duration_sec numeric,
  sample_rate_khz numeric,
  bitrate_kbps numeric,
  loudness_db numeric,
  noise_estimate text,
  created_at timestamptz NOT NULL DEFAULT now()
);

Row Level Security 
ALTER TABLE audio_submissions ENABLE ROW LEVEL SECURITY;

The 4 policies
CREATE POLICY "anon_select_audio_submissions"
  ON audio_submissions FOR SELECT
  TO anon, authenticated USING (true);

Storage 
INSERT INTO storage.buckets (id, name, public)
SELECT 'audio', 'audio', true
WHERE NOT EXISTS (SELECT 1 FROM storage.buckets WHERE id = 'audio');


Connecting to Bolt Database

import { createClient } from '@supabase/Bolt Database-js';
const url = import.meta.env.VITE_SUPABASE_URL as string;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;
export const Bolt Database = createClient(url, anonKey, {
  auth: { persistSession: false },
});
export type Submission = {
  id: string;
  submitter_name: string;
  phone: string;
  storage_path: string;
  file_name: string;
  mime_type: string;
  file_size: number;
  duration_sec: number | null;
  sample_rate_khz: number | null;
  bitrate_kbps: number | null;
  loudness_db: number | null;
  noise_estimate: string | null;
  created_at: string;
};

The Audio Analysis Engine

The type 
export type AudioAnalysis = {
  duration_sec: number;
  sample_rate_khz: number;
  bitrate_kbps: number;
  loudness_db: number;
  noise_estimate: string;
};

The noise labels
const noiseLabels = [
  { max: 30, label: 'Excellent (low noise)' },
  { max: 45, label: 'Good' },
  { max: 60, label: 'Fair (noticeable noise)' },
  { max: 75, label: 'Poor (noisy)' },
];

export async function analyzeAudio(file: File): Promise<AudioAnalysis> {
const arrayBuffer = await file.arrayBuffer();
const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
const audioBuffer = await audioContext.decodeAudioData(arrayBuffer.slice(0));
const duration_sec = audioBuffer.duration;
const sample_rate_khz = audioBuffer.sampleRate / 1000;
const channelData = audioBuffer.getChannelData(0);
const samples = channelData.length;

let sumSquares = 0;
let maxAbs = 0;
let firstZeroRun = 0;
let longestZeroRun = 0;
let zeroCount = 0;

for (let i = 0; i < samples; i++) {
  const v = channelData[i];
  sumSquares += v * v;
  const a = Math.abs(v);
  if (a > maxAbs) maxAbs = a;
  if (a < 0.005) {
    firstZeroRun++;
  } else {
    if (firstZeroRun > longestZeroRun) longestZeroRun = firstZeroRun;
    firstZeroRun = 0;
    zeroCount++;
  }
}
const rms = Math.sqrt(sumSquares / samples);
const loudness_db = 20 * Math.log10(rms + 1e-12);
const bytesPerSample = 2;
const channels = audioBuffer.numberOfChannels || 1;
const rawBitrate = audioBuffer.sampleRate * channels * bytesPerSample * 8;
const bitrate_kbps = Math.max(
  Math.round(rawBitrate / 1000),
  Math.round((file.size * 8) / duration_sec / 1000)
);
const silenceRatio = (samples - zeroCount) / samples;
let noiseScore = 0;
if (rms < 0.01) noiseScore += 35;
if (silenceRatio < 0.7) noiseScore += 20;
if (maxAbs < 0.1) noiseScore += 25;
if (rms > 0.0001 && rms < 0.05) noiseScore += 15;
noiseScore = Math.min(noiseScore, 100);

const label = noiseLabels.find((n) => noiseScore < n.max)?.label ?? 'Very poor (very noisy)';
await audioContext.close();

return {
  duration_sec: Math.round(duration_sec * 1000) / 1000,
  sample_rate_khz: Math.round(sample_rate_khz * 10) / 10,
  bitrate_kbps,
  loudness_db: Math.round(loudness_db * 100) / 100,
  noise_estimate: `${label} (noise score ${noiseScore}/100)`,
};

import { useState, useRef, useEffect } from 'react';
import { Mic, Square, Upload, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { Bolt Database, type Submission } from '@/lib/supabase';
import { analyzeAudio } from '@/lib/audioAnalysis';

type Status =
  | { kind: 'idle' }
  | { kind: 'analyzing' }
  | { kind: 'uploading' }
  | { kind: 'done' }
  | { kind: 'error'; message: string };

const [name, setName] = useState('');
const [phone, setPhone] = useState('');
const [file, setFile] = useState<File | null>(null);
const [previewUrl, setPreviewUrl] = useState<string | null>(null);
const [status, setStatus] = useState<Status>({ kind: 'idle' });

const [isRecording, setIsRecording] = useState(false);
const mediaRecorderRef = useRef<MediaRecorder | null>(null);
const chunksRef = useRef<Blob[]>([]);
const streamRef = useRef<MediaStream | null>(null);

useEffect(() => {
  return () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    streamRef.current?.getTracks().forEach((t) => t.stop());
  };
}, []);

async function startRecording() {
  setStatus({ kind: 'idle' });
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;
    const mr = new MediaRecorder(stream);
    chunksRef.current = [];
    mr.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    mr.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: mr.mimeType || 'audio/webm' });
      const recorded = new File([blob], `recording-${Date.now()}.webm`, { type: blob.type });
      pickFile(recorded);
      stream.getTracks().forEach((t) => t.stop());
    };

    mr.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: mr.mimeType || 'audio/webm' });
      const recorded = new File([blob], `recording-${Date.now()}.webm`, { type: blob.type });
      pickFile(recorded);
      stream.getTracks().forEach((t) => t.stop());
    };
    mr.start();
    mediaRecorderRef.current = mr;
    setIsRecording(true);
  } catch {
    setStatus({ kind: 'error', message: 'Could not access microphone...' });
  }
}
function stopRecording() {
  mediaRecorderRef.current?.stop();
  setIsRecording(false);
}
function pickFile(f: File | null) {
  if (!f) return;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  setFile(f);
  setPreviewUrl(URL.createObjectURL(f));
  setStatus({ kind: 'idle' });
}
function onFileInput(e: React.ChangeEvent<HTMLInputElement>) {
  pickFile(e.target.files?.[0] ?? null);
}
function valid(): boolean {
  return name.trim().length > 0 && phone.trim().length > 0 && !!file;
}
async function submit() {
  if (!valid() || !file) return;
  try {
    setStatus({ kind: 'analyzing' });
    const analysis = await analyzeAudio(file);
    setStatus({ kind: 'uploading' });
    const ext = file.name.split('.').pop()?.toLowerCase() || 'bin';
    const path = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}.${ext}`;
    const { error: upErr } = await supabase.storage.from('audio').upload(path, file, {
      contentType: file.type || 'application/octet-stream',
      upsert: false,
    });
    if (upErr) throw new Error(upErr.message);
    const { data, error: insErr } = await Bolt Database
      .from('audio_submissions')
      .insert({
        submitter_name: name.trim(),
        phone: phone.trim(),
        storage_path: path,
        file_name: file.name,
        mime_type: file.type || 'application/octet-stream',
        file_size: file.size,
        duration_sec: analysis.duration_sec,
        sample_rate_khz: analysis.sample_rate_khz,
        bitrate_kbps: analysis.bitrate_kbps,
        loudness_db: analysis.loudness_db,
        noise_estimate: analysis.noise_estimate,
      })
      .select()
      .single();
    if (insErr) throw new Error(insErr.message);

    setStatus({ kind: 'done' });
    setName('');
    setPhone('');
    setFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    onSubmitted(data as Submission);
  } catch (e) {
    setStatus({ kind: 'error', message: e instanceof Error ? e.message : 'Submission failed' });
  }
}
const busy = status.kind === 'analyzing' || status.kind === 'uploading';
function fmt(n: number | null, unit = '', digits = 2): string {
  if (n === null || n === undefined) return '—';
  return `${Number(n).toFixed(digits)}${unit}`;
}
function fmtDuration(sec: number | null): string {
  if (sec === null) return '—';
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}
const [rows, setRows] = useState<Submission[]>([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
const [playingId, setPlayingId] = useState<string | null>(null);
const [urls, setUrls] = useState<Record<string, string>>({});
const audioRef = useRef<HTMLAudioElement | null>(null);
useEffect(() => {
  let active = true;
  setLoading(true);
  setError(null);
  Bolt Database
    .from('audio_submissions')
    .select('*')
    .order('created_at', { ascending: false })
    .then(({ data, error }) => {
      if (!active) return;
      if (error) setError(error.message);
      else setRows(data as Submission[]);
      setLoading(false);
    });
  return () => {
    active = false;
  };
}, [refreshKey]);
async function ensureUrl(row: Submission): Promise<string | null> {
  if (urls[row.id]) return urls[row.id];
  const { data } = supabase.storage.from('audio').getPublicUrl(row.storage_path);
  const url = data.publicUrl;
  setUrls((prev) => ({ ...prev, [row.id]: url }));
  return url;
}
async function togglePlay(row: Submission) {
  let el = audioRef.current;

  if (playingId === row.id && el) {
    el.pause();
    setPlayingId(null);
    return;
  }
  if (el) {
    el.pause();
  }
  const url = await ensureUrl(row);
  if (!url) return;
  if (!el) {
    el = new Audio(url);
    el.onended = () => setPlayingId(null);
    audioRef.current = el;
  } else {
    el.src = url;
    el.load();
  }
  el.play().catch(() => {});
  setPlayingId(row.id);
}
import { useState } from 'react';
import { AudioWaveform } from 'lucide-react';
import SubmitForm from '@/components/SubmitForm';
import SubmissionsList from '@/components/SubmissionsList';
import type { Submission } from '@/lib/supabase';

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0);
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center gap-3 px-6 py-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-600 text-white">
            <AudioWaveform className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-base font-semibold leading-tight">Gig Audio Collector</h1>
            <p className="text-xs text-slate-500">Record or upload audio — we extract the technical details automatically.</p>
          </div>
        </div>
      </header>
      <main className="mx-auto grid max-w-5xl gap-6 px-6 py-8 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <SubmitForm onSubmitted={() => setRefreshKey((k) => k + 1)} />
        </div>
        <div className="lg:col-span-3">
          <SubmissionsList refreshKey={refreshKey} />
        </div>
      </main>
      <footer className="mx-auto max-w-5xl px-6 pb-8 text-center text-xs text-slate-400">
        Audio analysis runs entirely in your browser via the Web Audio API.
      </footer>
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
<title>Gig Audio Collector</title>
resolve: {
  alias: {
    '@': fileURLToPath(new URL('./src', import.meta.url)),
  },
},
optimizeDeps: {
  exclude: ['lucide-react'],
},
content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
