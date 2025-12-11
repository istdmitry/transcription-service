"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Button, Card } from '@/components/ui';

export default function Dashboard() {
    const router = useRouter();
    const [transcripts, setTranscripts] = useState<any[]>([]);
    const [uploading, setUploading] = useState(false);
    const [apiKey, setApiKey] = useState("");

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            router.push('/');
            return;
        }
        loadTranscripts(token);
        api.getProfile(token).then(u => u && setApiKey(u.api_key));
    }, []);

    const loadTranscripts = async (token: string) => {
        try {
            const data = await api.getTranscripts(token);
            setTranscripts(data);
        } catch (e) {
            console.error(e);
            // If error (e.g. 401), redirect to login
            router.push('/');
        }
    };

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        const token = localStorage.getItem('token');
        try {
            if (token) {
                await api.uploadFile(token, file);
                await loadTranscripts(token); // Refresh
            }
        } catch (err) {
            alert("Upload failed");
        } finally {
            setUploading(false);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed': return 'text-green-400';
            case 'processing': return 'text-yellow-400';
            case 'failed': return 'text-red-400';
            default: return 'text-slate-400';
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm("Are you sure you want to delete this transcript?")) return;
        try {
            const token = localStorage.getItem("token");
            if (token) {
                await api.deleteTranscript(token, id);
                setTranscripts(transcripts.filter((t) => t.id !== id));
            }
        } catch (err) {
            alert("Failed to delete");
        }
    };

    return (
        <main className="min-h-screen p-8">
            <div className="max-w-6xl mx-auto">
                <header className="flex justify-between items-end mb-10">
                    <div>
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">Dashboard</h1>
                        <p className="text-slate-400 mb-2">Manage your transcripts</p>
                        {apiKey && (
                            <div className="text-xs bg-slate-800 p-2 rounded border border-slate-700 inline-block font-mono text-slate-300">
                                API Key: <span className="select-all text-violet-300">{apiKey}</span>
                            </div>
                        )}
                    </div>
                    <div className="relative">
                        <input
                            type="file"
                            id="file-upload"
                            className="hidden"
                            onChange={handleUpload}
                            accept="audio/*,video/*"
                            disabled={uploading}
                        />
                        <label htmlFor="file-upload">
                            <div className={`cursor-pointer px-6 py-3 rounded-lg font-medium bg-violet-600 hover:bg-violet-500 text-white transition-all shadow-lg shadow-violet-500/20 ${uploading ? 'opacity-50' : ''}`}>
                                {uploading ? 'Uploading...' : '+ Upload New File'}
                            </div>
                        </label>
                    </div>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {transcripts.map((t) => (
                        <Card key={t.id} className="hover:bg-slate-800/50 transition-colors group">
                            <div className="flex justify-between items-start mb-4">
                                <div className={`text-xs font-mono px-2 py-1 rounded bg-slate-800 ${getStatusColor(t.status)}`}>
                                    {t.status.toUpperCase()}
                                </div>
                                <span className="text-slate-500 text-xs">{new Date(t.created_at).toLocaleDateString()}</span>
                            </div>
                            <h3 className="font-semibold text-lg text-slate-100 mb-2 truncate" title={t.filename}>
                                {t.filename}
                            </h3>
                            <p className="text-slate-400 text-sm line-clamp-3 mb-4 h-15">
                                {t.transcript_text || "Waiting for transcription..."}
                            </p>
                            <div className="flex justify-end">
                                <Button variant="outline" className="text-xs py-1" onClick={() => router.push(`/transcripts/${t.id}`)}>
                                    View Details
                                </Button>
                            </div>
                        </Card>
                    ))}
                </div>

                {transcripts.length === 0 && (
                    <div className="text-center py-20 text-slate-500">
                        <p>No transcripts found. Upload a file to get started.</p>
                    </div>
                )}
            </div>
        </main>
    );
}
