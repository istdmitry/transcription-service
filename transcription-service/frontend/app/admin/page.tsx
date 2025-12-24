"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Button } from '@/components/ui';

export default function AdminPanel() {
    const router = useRouter();
    const [users, setUsers] = useState<any[]>([]);
    const [stats, setStats] = useState<any>(null);
    const [projects, setProjects] = useState<any[]>([]);
    const [newProject, setNewProject] = useState({ name: '', description: '', gdrive_folder: '', gdrive_creds: '' });
    const [assignment, setAssignment] = useState({ projectId: '', userId: '', role: 'member' });
    const [projectDrive, setProjectDrive] = useState({ projectId: '', gdrive_folder: '', gdrive_creds: '' });
    const [loading, setLoading] = useState(true);
    const [savingProject, setSavingProject] = useState(false);
    const [assigning, setAssigning] = useState(false);
    const [updatingDrive, setUpdatingDrive] = useState(false);

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
            const [u, s, p] = await Promise.all([
                api.getAdminUsers(token),
                api.getAdminStats(token),
                api.getProjectsAdmin(token)
            ]);
            setUsers(u);
            setStats(s);
            setProjects(p);
        } catch (e) {
            alert("Unauthorized access");
            router.push('/dashboard');
        } finally {
            setLoading(false);
        }
    };

    const handleCreateProject = async () => {
        if (!newProject.name.trim()) {
            alert("Project name is required");
            return;
        }
        const token = localStorage.getItem('token');
        if (!token) return;

        try {
            setSavingProject(true);
            await api.createProject(token, newProject);
            const refreshed = await api.getProjectsAdmin(token);
            setProjects(refreshed);
            setNewProject({ name: '', description: '', gdrive_folder: '', gdrive_creds: '' });
            alert("Project created");
        } catch (e) {
            alert("Failed to create project");
        } finally {
            setSavingProject(false);
        }
    };

    const handleAssignUser = async () => {
        if (!assignment.projectId || !assignment.userId) {
            alert("Select project and user");
            return;
        }
        const token = localStorage.getItem('token');
        if (!token) return;
        try {
            setAssigning(true);
            await api.addProjectMember(token, parseInt(assignment.projectId), {
                user_id: parseInt(assignment.userId),
                role: assignment.role
            });
            const refreshed = await api.getProjectsAdmin(token);
            setProjects(refreshed);
            alert("User assigned");
        } catch (e) {
            alert("Failed to assign user");
        } finally {
            setAssigning(false);
        }
    };

    const handleUpdateProjectDrive = async () => {
        if (!projectDrive.projectId) {
            alert("Select a project to update");
            return;
        }
        const token = localStorage.getItem('token');
        if (!token) return;
        try {
            setUpdatingDrive(true);
            await api.updateProject(token, parseInt(projectDrive.projectId), {
                gdrive_folder: projectDrive.gdrive_folder,
                gdrive_creds: projectDrive.gdrive_creds || undefined
            });
            const refreshed = await api.getProjectsAdmin(token);
            setProjects(refreshed);
            setProjectDrive({ projectId: '', gdrive_folder: '', gdrive_creds: '' });
            alert("Drive settings updated");
        } catch (e) {
            alert("Failed to update project drive");
        } finally {
            setUpdatingDrive(false);
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

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-10">
                    <div className="bg-[#0d1117] border border-[#30363d] rounded-xl p-6">
                        <h3 className="text-lg font-bold text-white mb-4">Create Project</h3>
                        <div className="space-y-3">
                            <input
                                className="w-full bg-[#0a0c10] border border-[#30363d] rounded px-3 py-2 text-sm"
                                placeholder="Project name"
                                value={newProject.name}
                                onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                            />
                            <textarea
                                className="w-full bg-[#0a0c10] border border-[#30363d] rounded px-3 py-2 text-sm"
                                placeholder="Description"
                                value={newProject.description}
                                onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                            />
                            <input
                                className="w-full bg-[#0a0c10] border border-[#30363d] rounded px-3 py-2 text-sm"
                                placeholder="Google Drive Folder ID"
                                value={newProject.gdrive_folder}
                                onChange={(e) => setNewProject({ ...newProject, gdrive_folder: e.target.value })}
                            />
                            <textarea
                                className="w-full bg-[#0a0c10] border border-[#30363d] rounded px-3 py-2 text-sm font-mono"
                                placeholder="Service Account JSON (optional, stored encrypted)"
                                rows={4}
                                value={newProject.gdrive_creds}
                                onChange={(e) => setNewProject({ ...newProject, gdrive_creds: e.target.value })}
                            />
                            <Button onClick={handleCreateProject} disabled={savingProject}>
                                {savingProject ? "Creating..." : "Create Project"}
                            </Button>
                        </div>
                    </div>

                    <div className="bg-[#0d1117] border border-[#30363d] rounded-xl p-6">
                        <h3 className="text-lg font-bold text-white mb-4">Assign User to Project</h3>
                        <div className="space-y-3">
                            <select
                                className="w-full bg-[#0a0c10] border border-[#30363d] rounded px-3 py-2 text-sm"
                                value={assignment.projectId}
                                onChange={(e) => setAssignment({ ...assignment, projectId: e.target.value })}
                            >
                                <option value="">Select Project</option>
                                {projects.map((p) => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </select>
                            <select
                                className="w-full bg-[#0a0c10] border border-[#30363d] rounded px-3 py-2 text-sm"
                                value={assignment.userId}
                                onChange={(e) => setAssignment({ ...assignment, userId: e.target.value })}
                            >
                                <option value="">Select User</option>
                                {users.map((u) => (
                                    <option key={u.id} value={u.id}>{u.email}</option>
                                ))}
                            </select>
                            <select
                                className="w-full bg-[#0a0c10] border border-[#30363d] rounded px-3 py-2 text-sm"
                                value={assignment.role}
                                onChange={(e) => setAssignment({ ...assignment, role: e.target.value })}
                            >
                                <option value="member">Member</option>
                                <option value="admin">Admin</option>
                            </select>
                            <Button onClick={handleAssignUser} disabled={assigning}>
                                {assigning ? "Assigning..." : "Assign User"}
                            </Button>
                        </div>
                    </div>

                    <div className="bg-[#0d1117] border border-[#30363d] rounded-xl p-6">
                        <h3 className="text-lg font-bold text-white mb-4">Connect Project to Google Drive</h3>
                        <div className="space-y-3">
                            <select
                                className="w-full bg-[#0a0c10] border border-[#30363d] rounded px-3 py-2 text-sm"
                                value={projectDrive.projectId}
                                onChange={(e) => setProjectDrive({ ...projectDrive, projectId: e.target.value })}
                            >
                                <option value="">Select Project</option>
                                {projects.map((p) => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </select>
                            <input
                                className="w-full bg-[#0a0c10] border border-[#30363d] rounded px-3 py-2 text-sm"
                                placeholder="Google Drive Folder ID"
                                value={projectDrive.gdrive_folder}
                                onChange={(e) => setProjectDrive({ ...projectDrive, gdrive_folder: e.target.value })}
                            />
                            <textarea
                                className="w-full bg-[#0a0c10] border border-[#30363d] rounded px-3 py-2 text-sm font-mono"
                                placeholder="Service Account JSON (optional, stored encrypted)"
                                rows={4}
                                value={projectDrive.gdrive_creds}
                                onChange={(e) => setProjectDrive({ ...projectDrive, gdrive_creds: e.target.value })}
                            />
                            <Button onClick={handleUpdateProjectDrive} disabled={updatingDrive}>
                                {updatingDrive ? "Saving..." : "Save Drive Settings"}
                            </Button>
                        </div>
                    </div>
                </div>

                <div className="bg-[#0d1117] border border-[#30363d] rounded-xl overflow-hidden mb-12">
                    <div className="p-6 border-b border-[#30363d] bg-[#161b22] flex justify-between items-center">
                        <h2 className="font-bold text-lg text-white">Projects</h2>
                        <span className="text-xs text-slate-500">GDrive: stored encrypted</span>
                    </div>
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-[#0a0b10] border-b border-[#30363d] text-slate-500 text-xs uppercase tracking-widest">
                                <th className="px-6 py-4">Name</th>
                                <th className="px-6 py-4">Drive</th>
                                <th className="px-6 py-4">Members</th>
                                <th className="px-6 py-4 text-right">Created</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[#30363d]">
                            {projects.map((p) => (
                                <tr key={p.id} className="hover:bg-[#161b22]/50 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="font-semibold text-slate-100">{p.name}</div>
                                        <div className="text-[11px] text-slate-500">{p.description || 'No description'}</div>
                                    </td>
                                    <td className="px-6 py-4 text-sm">
                                        <div className="text-slate-300">{p.gdrive_folder || 'No folder set'}</div>
                                        <div className={`text-[11px] ${p.has_gdrive_creds ? 'text-green-500' : 'text-slate-500'}`}>
                                            {p.has_gdrive_creds ? 'Service account stored' : 'Credentials missing'}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-sm">
                                        <div className="flex flex-wrap gap-2">
                                            {p.members?.length ? p.members.map((m: any) => (
                                                <span key={`${p.id}-${m.user_id}`} className="px-2 py-0.5 text-[11px] rounded bg-slate-800 border border-slate-700 text-slate-200">
                                                    {m.email} ({m.role})
                                                </span>
                                            )) : <span className="text-xs text-slate-500">No members</span>}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-right text-sm text-slate-500">
                                        {new Date(p.created_at).toLocaleDateString()}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

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
