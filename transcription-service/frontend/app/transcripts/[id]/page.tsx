"use client";
import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { Button, Card } from '@/components/ui';

export default function TranscriptDetail() {
    const router = useRouter();
    const params = useParams();
    const [transcript, setTranscript] = useState<any>(null);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            router.push('/');
            return;
        }

        if (params.id) {
            api.getTranscript(token, params.id as string)
                .then(data => setTranscript(data))
                .catch(err => {
                    console.error(err);
                    router.push('/dashboard');
                });
        }
    }, [params.id, router]);

    if (!transcript) return <div className="p-10 text-center text-slate-500">Loading...</div>;

    return (
        <main className="min-h-screen p-8">
            <div className="max-w-4xl mx-auto">
                <Button onClick={() => router.push('/dashboard')} variant="secondary" className="mb-6">
                    ← Back to Dashboard
                </Button>

                <Card>
                    <h1 className="text-2xl font-bold mb-2 text-violet-400">{transcript.filename}</h1>
                    <div className="flex gap-4 text-sm text-slate-500 mb-6">
                        <span>Created: {new Date(transcript.created_at).toLocaleString()}</span>
                        <span className="uppercase">{transcript.status}</span>
                        <span className="uppercase">{transcript.language || 'EN'}</span>
                    </div>

                    <div className="bg-slate-900 rounded-lg p-6 min-h-[300px] whitespace-pre-wrap text-slate-200 leading-relaxed">
                        {transcript.status === 'failed' ? (
                            <div className="text-red-400 border border-red-900/50 bg-red-900/20 p-4 rounded">
                                <h3 className="font-bold mb-2">Transcription Failed</h3>
                                <p>{transcript.error_message || "Unknown error occurred."}</p>
                            </div>
                        ) : (
                            transcript.transcript_text || "Transcription in progress..."
                        )}
                    </div>

                    {transcript.media_url && (
                        <div className="mt-8">
                            <h3 className="text-sm font-medium text-slate-400 mb-2">Original Metadata</h3>
                            <code className="bg-black/30 p-2 rounded text-xs block overflow-auto text-violet-200">
                                {transcript.media_url}
                            </code>
                        </div>
                    )}
                </Card>
            </div>
        </main>
    );
}
