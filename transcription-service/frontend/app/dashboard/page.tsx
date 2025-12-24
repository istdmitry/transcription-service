"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Button } from '@/components/ui';

export default function Dashboard() {
    const router = useRouter();
    const [user, setUser] = useState<any | null>(null);
    const [projects, setProjects] = useState<any[]>([]);
    const [transcripts, setTranscripts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [filterStatus, setFilterStatus] = useState<string>("");
    const [filterProject, setFilterProject] = useState<string>("");
    const [sortBy, setSortBy] = useState<string>("created_at_desc");
    const [personalDrive, setPersonalDrive] = useState({ folder: '', creds: '', email: '' });

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            router.push('/');
            return;
        }
        init(token);
    }, []);

    // Effect to reload when filters change
    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token && user) { // Only reload if user loaded
            loadTranscripts(token);
        }
    }, [filterStatus, filterProject, sortBy]);

    const loadTranscripts = async (token: string) => {
        try {
            setLoading(true);
            const projectId = filterProject === "personal" ? undefined : (filterProject ? parseInt(filterProject) : undefined);
            const t = await api.getTranscripts(token, {
                status: filterStatus || undefined,
                project_id: projectId,
                sort_by: sortBy
            });
            setTranscripts(t);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const init = async (token: string) => {
        try {
            const [u, p] = await Promise.all([
                api.getProfile(token),
                api.getProjects(token)
            ]);
            setUser(u);
            setProjects(p);
            setPersonalDrive({
                folder: u?.gdrive_folder || '',
                creds: '',
                email: u?.gdrive_email || ''
            });
            // Load transcripts after projects to ensure we have filters ready if needed (though we default to empty)
            await loadTranscripts(token);
        } catch (e) {
            console.error(e);
            router.push('/');
        } finally {
            setLoading(false);
        }
    };

    const handleCreateProject = async () => {
        const name = prompt("Enter project name:");
        if (!name) return;
        const description = prompt("Enter description (optional):") || "";
        const folder = prompt("Enter Google Drive Folder ID (optional):") || "";

        try {
            const token = localStorage.getItem("token");
            if (token) {
                await api.createProject(token, { name, description, gdrive_folder: folder });
                const p = await api.getProjects(token);
                setProjects(p);
                alert("Project created!");
            }
        } catch (e) {
            alert("Failed to create project");
        }
    };

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const token = localStorage.getItem('token');
        if (!token) return;

        try {
            setUploading(true);
            await api.uploadFile(token, file);
            await loadTranscripts(token);
        } catch (err) {
            alert("Upload failed");
        } finally {
            setUploading(false);
            e.target.value = "";
        }
    };

    const handleReassign = async (transcript: any, projectId: number | null) => {
        const token = localStorage.getItem('token');
        if (!token) return;
        try {
            await api.reassignTranscript(token, transcript.id, projectId);
            await loadTranscripts(token);
        } catch (e) {
            alert("Failed to reassign transcript");
        }
    };

    const handleDelete = async (transcript: any) => {
        const token = localStorage.getItem('token');
        if (!token) return;
        if (!confirm("Delete this transcript?")) return;
        try {
            await api.deleteTranscript(token, transcript.id);
            await loadTranscripts(token);
        } catch (e) {
            alert("Failed to delete transcript");
        }
    };

    const handleSavePersonalDrive = async () => {
        const token = localStorage.getItem('token');
        if (!token) return;
        try {
            const updated = await api.updateMyGDrive(token, {
                gdrive_folder: personalDrive.folder,
                gdrive_creds: personalDrive.creds || undefined,
                gdrive_email: personalDrive.email || undefined
            });
            setUser(updated);
            setPersonalDrive({ folder: updated.gdrive_folder || '', creds: '', email: updated.gdrive_email || '' });
            alert("Personal Google Drive updated");
        } catch (e) {
            alert("Failed to update Drive settings");
        }
    };

    if (loading && !user) return <div className="p-20 text-center text-slate-400">Loading your workspace...</div>;

    return (
        <main className="min-h-screen p-8 bg-[#0a0c10] text-[#c9d1d9]">
            <div className="max-w-7xl mx-auto">
                <header className="flex justify-between items-start mb-8">
                    <div>
                        <div className="flex items-center gap-4 mb-2">
                            <h1 className="text-4xl font-extrabold tracking-tight text-white">Workspace</h1>
                            {user?.is_admin && (
                                <>
                                    <button onClick={() => router.push('/admin')} className="text-xs px-2 py-1 bg-amber-500/10 text-amber-500 border border-amber-500/20 rounded hover:bg-amber-500/20 transition-colors">
                                        ADMIN PANEL
                                    </button>
                                    <button onClick={handleCreateProject} className="text-xs px-2 py-1 bg-blue-500/10 text-blue-500 border border-blue-500/20 rounded hover:bg-blue-500/20 transition-colors ml-2">
                                        + NEW PROJECT
                                    </button>
                                </>
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

                {/* Personal Google Drive */}
                <div className="bg-[#0d1117] border border-[#30363d] rounded-xl p-4 mb-6">
                    <div className="flex justify-between items-center mb-3">
                        <div>
                            <div className="text-sm text-slate-400">Personal Google Drive</div>
                            <div className={`text-xs ${user?.has_gdrive_creds ? 'text-green-500' : 'text-slate-500'}`}>
                                {user?.has_gdrive_creds ? 'Service account stored' : 'Credentials not connected'}
                            </div>
                        </div>
                        <Button onClick={handleSavePersonalDrive}>Save</Button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <input
                            className="w-full bg-[#0a0c10] border border-[#30363d] rounded px-3 py-2 text-sm"
                            placeholder="Google Drive Folder ID"
                            value={personalDrive.folder}
                            onChange={(e) => setPersonalDrive({ ...personalDrive, folder: e.target.value })}
                        />
                        <input
                            className="w-full bg-[#0a0c10] border border-[#30363d] rounded px-3 py-2 text-sm"
                            placeholder="Service Account Email"
                            value={personalDrive.email}
                            onChange={(e) => setPersonalDrive({ ...personalDrive, email: e.target.value })}
                        />
                        <textarea
                            className="w-full bg-[#0a0c10] border border-[#30363d] rounded px-3 py-2 text-sm font-mono"
                            placeholder="Service Account JSON (optional, stored encrypted)"
                            rows={3}
                            value={personalDrive.creds}
                            onChange={(e) => setPersonalDrive({ ...personalDrive, creds: e.target.value })}
                        />
                    </div>
                    <p className="text-[11px] text-slate-500 mt-2">Leave credentials empty to keep existing. Folder determines where personal transcripts are exported.</p>
                </div>

                {/* Filters */}
                <div className="flex flex-wrap gap-4 mb-6 p-4 bg-[#161b22] border border-[#30363d] rounded-lg items-center">
                    <div className="text-sm font-semibold text-slate-400">Filters:</div>

                    <select
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                        className="bg-[#0d1117] border border-[#30363d] text-sm rounded px-3 py-1.5 text-slate-300 outline-none focus:border-blue-500"
                    >
                        <option value="">All Statuses</option>
                        <option value="completed">Completed</option>
                        <option value="processing">Processing</option>
                        <option value="failed">Failed</option>
                        <option value="pending">Pending</option>
                    </select>

                    <select
                        value={filterProject}
                        onChange={(e) => setFilterProject(e.target.value)}
                        className="bg-[#0d1117] border border-[#30363d] text-sm rounded px-3 py-1.5 text-slate-300 outline-none focus:border-blue-500"
                    >
                        <option value="">All Projects</option>
                        <option value="personal">Personal only</option>
                        {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                    </select>

                    <div className="w-px h-6 bg-[#30363d] mx-2"></div>

                    <div className="text-sm font-semibold text-slate-400">Sort:</div>
                    <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="bg-[#0d1117] border border-[#30363d] text-sm rounded px-3 py-1.5 text-slate-300 outline-none focus:border-blue-500"
                    >
                        <option value="created_at_desc">Newest First</option>
                        <option value="created_at_asc">Oldest First</option>
                        <option value="filename_asc">Filename A-Z</option>
                        <option value="filename_desc">Filename Z-A</option>
                    </select>
                </div>

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
                                        {t.gdrive_error_message && (
                                            <div className="text-[11px] text-red-400 mt-1">
                                                GDrive: {t.gdrive_error_message}
                                            </div>
                                        )}
                                        {!t.gdrive_error_message && t.gdrive_file_id && (
                                            <div className="text-[11px] text-green-500 mt-1">GDrive: uploaded</div>
                                        )}
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

