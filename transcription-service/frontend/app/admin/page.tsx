"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Button } from '@/components/ui';

export default function AdminPanel() {
    const router = useRouter();
    const [users, setUsers] = useState<any[]>([]);
    const [stats, setStats] = useState<any>(null);
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
            const [u, s] = await Promise.all([
                api.getAdminUsers(token),
                api.getAdminStats(token)
            ]);
            setUsers(u);
            setStats(s);
        } catch (e) {
            alert("Unauthorized access");
            router.push('/dashboard');
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-20 text-center text-slate-400">Loading Admin Panel...</div>;

    return (
        <main className="min-h-screen p-8 bg-[#0a0c10] text-[#c9d1d9]">
            <div className="max-w-7xl mx-auto">
                <header className="flex justify-between items-start mb-12">
                    <div>
                        <button
                            onClick={() => router.push('/dashboard')}
                            className="text-xs text-slate-500 hover:text-white mb-4 flex items-center gap-1"
                        >
                            ← BACK TO WORKSPACE
                        </button>
                        <h1 className="text-4xl font-extrabold tracking-tight text-white mb-2">Admin Control</h1>
                        <p className="text-slate-400">Manage users, projects, and monitor performance</p>
                    </div>

                    <div className="grid grid-cols-3 gap-6">
                        <div className="bg-[#161b22] border border-[#30363d] rounded p-4 text-center">
                            <div className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-1">Users</div>
                            <div className="text-2xl font-bold text-white">{stats?.total_users || 0}</div>
                        </div>
                        <div className="bg-[#161b22] border border-[#30363d] rounded p-4 text-center">
                            <div className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-1">Transcripts</div>
                            <div className="text-2xl font-bold text-white">{stats?.total_transcripts || 0}</div>
                        </div>
                        <div className="bg-[#161b22] border border-[#30363d] rounded p-4 text-center">
                            <div className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-1">Projects</div>
                            <div className="text-2xl font-bold text-white">{stats?.total_projects || 0}</div>
                        </div>
                    </div>
                </header>

                <div className="bg-[#0d1117] border border-[#30363d] rounded-xl overflow-hidden mb-12">
                    <div className="p-6 border-b border-[#30363d] bg-[#161b22]">
                        <h2 className="font-bold text-lg text-white">Identity Management</h2>
                    </div>
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-[#0a0b10] border-b border-[#30363d] text-slate-500 text-xs uppercase tracking-widest">
                                <th className="px-6 py-4">User</th>
                                <th className="px-6 py-4">Phone</th>
                                <th className="px-6 py-4">Projects</th>
                                <th className="px-6 py-4">Activity</th>
                                <th className="px-6 py-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[#30363d]">
                            {users.map((u) => (
                                <tr key={u.id} className="hover:bg-[#161b22]/50 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="font-semibold text-slate-100">{u.email}</div>
                                        <div className="text-[10px] text-slate-500 italic">ID: {u.id} • Registered {new Date(u.created_at).toLocaleDateString()}</div>
                                    </td>
                                    <td className="px-6 py-4 text-sm font-mono text-slate-400">
                                        {u.phone_number || "Not Linked"}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex flex-wrap gap-1">
                                            {u.projects.length > 0 ? u.projects.map((p: string) => (
                                                <span key={p} className="text-[10px] px-2 py-0.5 bg-violet-500/10 text-violet-400 border border-violet-500/20 rounded">
                                                    {p.toUpperCase()}
                                                </span>
                                            )) : <span className="text-[10px] text-slate-600">PERSONAL ONLY</span>}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="text-xs text-slate-400">Total: <span className="text-slate-100 font-bold">{u.total_transcripts}</span></div>
                                        {u.last_transcript_at && (
                                            <div className="text-[10px] text-slate-500">Last: {new Date(u.last_transcript_at).toLocaleDateString()}</div>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button className="text-xs text-sky-500 hover:text-sky-400 font-bold tracking-tight">MANAGE ACCESS</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
    );
}
