"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Button } from '@/components/ui';

export default function Dashboard() {
    const router = useRouter();
    const [transcripts, setTranscripts] = useState<any[]>([]);
    const [projects, setProjects] = useState<any[]>([]);
    const [user, setUser] = useState<any>(null);
    const [uploading, setUploading] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            router.push('/');
            return;
        }
        init(token);
    }, []);

    const init = async (token: string) => {
        try {
            const [u, t, p] = await Promise.all([
                api.getProfile(token),
                api.getTranscripts(token),
                api.getProjects(token)
            ]);
            setUser(u);
            setTranscripts(t);
            setProjects(p);
        } catch (e) {
            console.error(e);
            router.push('/');
        } finally {
            setLoading(false);
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
                const t = await api.getTranscripts(token);
                setTranscripts(t);
            }
        } catch (err) {
            alert("Upload failed");
        } finally {
            setUploading(false);
        }
    };

    const handleDelete = async (t: any) => {
        let msg = "Are you sure you want to delete this transcript?";
        if (t.gdrive_file_id) {
            msg += "\n\n⚠️ WARNING: This transcript has been exported to Google Drive. Deleting it here will NOT remove it from your GDrive.";
        }

        if (!confirm(msg)) return;

        try {
            const token = localStorage.getItem("token");
            if (token) {
                await api.deleteTranscript(token, t.id);
                setTranscripts(transcripts.filter((x) => x.id !== t.id));
            }
        } catch (err) {
            alert("Failed to delete");
        }
    };

    const handleReassign = async (t: any, projectId: number | null) => {
        if (t.gdrive_file_id) {
            const msg = "⚠️ This transcript was already uploaded to Google Drive. Reassigning will NOT move or remove the file in the external folder.";
            if (!confirm(msg)) return;
        }

        try {
            const token = localStorage.getItem("token");
            if (token) {
                await api.reassignTranscript(token, t.id, projectId);
                const updated = await api.getTranscripts(token);
                setTranscripts(updated);
            }
        } catch (err) {
            alert("Failed to reassign");
        }
    };

    if (loading) return <div className="p-20 text-center text-slate-400">Loading your workspace...</div>;

    return (
        <main className="min-h-screen p-8 bg-[#0a0c10] text-[#c9d1d9]">
            <div className="max-w-7xl mx-auto">
                <header className="flex justify-between items-start mb-12">
                    <div>
                        <div className="flex items-center gap-4 mb-2">
                            <h1 className="text-4xl font-extrabold tracking-tight text-white">Workspace</h1>
                            {user?.is_admin && (
                                <button onClick={() => router.push('/admin')} className="text-xs px-2 py-1 bg-amber-500/10 text-amber-500 border border-amber-500/20 rounded hover:bg-amber-500/20 transition-colors">
                                    ADMIN PANEL
                                </button>
                            )}
                        </div>
                        <p className="text-slate-400">Manage and organize your transcriptions</p>
                    </div>

                    <div className="flex gap-3">
                        <Button variant="outline" onClick={() => router.push('/instructions')} className="border-slate-700 text-slate-300 hover:bg-slate-800">
                            Setup Instructions
                        </Button>
                        <div className="relative">
                            <input type="file" id="file-upload" className="hidden" onChange={handleUpload} accept="audio/*,video/*" disabled={uploading} />
                            <label htmlFor="file-upload">
                                <div className={`cursor-pointer px-6 py-2 rounded font-bold bg-[#238636] hover:bg-[#2ea043] text-white transition-all shadow-lg ${uploading ? 'opacity-50' : ''}`}>
                                    {uploading ? 'UPLOADING...' : 'NEW TRANSCRIPTION'}
                                </div>
                            </label>
                        </div>
                    </div>
                </header>

                <div className="bg-[#0d1117] border border-[#30363d] rounded-xl overflow-hidden">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-[#161b22] border-b border-[#30363d] text-slate-400 text-sm">
                                <th className="px-6 py-4 font-semibold">Date</th>
                                <th className="px-6 py-4 font-semibold">Filename</th>
                                <th className="px-6 py-4 font-semibold">Project / Assignment</th>
                                <th className="px-6 py-4 font-semibold">Status</th>
                                <th className="px-6 py-4 font-semibold text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[#30363d]">
                            {transcripts.map((t) => (
                                <tr key={t.id} className="hover:bg-[#161b22]/50 transition-colors group">
                                    <td className="px-6 py-4 text-xs font-mono text-slate-500 whitespace-nowrap">
                                        {new Date(t.created_at).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="font-semibold text-slate-100 truncate max-w-[300px]" title={t.filename}>
                                            {t.filename}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <select
                                            value={t.project_id || ""}
                                            onChange={(e) => handleReassign(t, e.target.value ? parseInt(e.target.value) : null)}
                                            className="bg-[#0d1117] border border-[#30363d] text-sm rounded px-3 py-1 text-slate-300 focus:ring-1 focus:ring-violet-500 outline-none"
                                        >
                                            <option value="">Personal Note</option>
                                            {projects.map(p => (
                                                <option key={p.id} value={p.id}>{p.name}</option>
                                            ))}
                                        </select>
                                    </td>
                                    <td className="px-6 py-4 text-sm font-medium">
                                        <div className="flex items-center gap-2">
                                            <span className={`w-2 h-2 rounded-full ${t.status === 'completed' ? 'bg-green-500' :
                                                    t.status === 'processing' ? 'bg-yellow-500 animate-pulse' : 'bg-red-500'
                                                }`} />
                                            {t.status.toUpperCase()}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="flex justify-end gap-2">
                                            <button
                                                onClick={() => router.push(`/transcripts/${t.id}`)}
                                                className="text-xs text-slate-400 hover:text-white underline underline-offset-4"
                                            >
                                                DETAILS
                                            </button>
                                            <button
                                                onClick={() => handleDelete(t)}
                                                className="text-xs text-red-500/70 hover:text-red-400 ml-4"
                                            >
                                                DELETE
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>

                    {transcripts.length === 0 && (
                        <div className="text-center py-24 text-slate-500">
                            <div className="text-5xl mb-4">📝</div>
                            <p className="text-lg">No transcriptions found in this workspace.</p>
                            <p className="text-sm">Upload a file or use the Telegram bot to get started.</p>
                        </div>
                    )}
                </div>

                <footer className="mt-12 pt-8 border-t border-[#30363d] flex justify-between text-xs text-slate-500">
                    <div>
                        Connected as: <span className="text-slate-300">{user?.email}</span>
                    </div>
                    <div className="flex gap-6">
                        <span>API Status: Online</span>
                        <span>Projects Active: {projects.length}</span>
                    </div>
                </footer>
            </div>
        </main>
    );
}

