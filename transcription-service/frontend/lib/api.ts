const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = {
    async login(email: string, password: string) {
        const formData = new FormData();
        formData.append('username', email); // OAuth2 expects username
        formData.append('password', password);

        const res = await fetch(`${API_URL}/auth/token`, {
            method: 'POST',
            body: formData,
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Login failed');
        }
        return res.json();
    },

    async register(email: string, password: string, phone_number?: string) {
        const res = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, phone_number }),
        });

        if (!res.ok) {
            throw new Error('Registration failed');
        }
        return res.json();
    },

    async getProfile(token: string) {
        const res = await fetch(`${API_URL}/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) return null;
        return res.json();
    },

    async getTranscripts(token: string, filters?: { status?: string, project_id?: number, sort_by?: string }) {
        const params = new URLSearchParams();
        if (filters?.status) params.append('status', filters.status);
        if (filters?.project_id) params.append('project_id', filters.project_id.toString());
        if (filters?.sort_by) params.append('sort_by', filters.sort_by);

        const res = await fetch(`${API_URL}/transcripts/?${params.toString()}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return res.json();
    },

    async getTranscript(token: string, id: string) {
        const res = await fetch(`${API_URL}/transcripts/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch transcript');
        return res.json();
    },

    async deleteTranscript(token: string, id: number) {
        const res = await fetch(`${API_URL}/transcripts/${id}`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error("Failed to delete transcript");
    },

    async uploadFile(token: string, file: File) {
        const formData = new FormData();
        formData.append('file', file);

        const res = await fetch(`${API_URL}/transcripts/`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (!res.ok) throw new Error('Upload failed');
        return res.json();
    },

    async reassignTranscript(token: string, id: number, project_id: number | null) {
        const res = await fetch(`${API_URL}/transcripts/${id}/reassign`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ project_id })
        });
        if (!res.ok) throw new Error('Reassign failed');
        return res.json();
    },

    // --- Projects ---
    async getProjects(token: string) {
        const res = await fetch(`${API_URL}/projects/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return res.json();
    },

    async getProjectsAdmin(token: string) {
        const res = await fetch(`${API_URL}/projects/admin`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return res.json();
    },

    async createProject(token: string, data: any) {
        const res = await fetch(`${API_URL}/projects/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        return res.json();
    },

    async updateProject(token: string, id: number, data: any) {
        const res = await fetch(`${API_URL}/projects/${id}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        return res.json();
    },

    async addProjectMember(token: string, projectId: number, data: any) {
        const res = await fetch(`${API_URL}/projects/${projectId}/members`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        return res.json();
    },

    // --- Admin ---
    async getAdminUsers(token: string) {
        const res = await fetch(`${API_URL}/admin/users`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return res.json();
    },

    async getAdminStats(token: string) {
        const res = await fetch(`${API_URL}/admin/stats`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return res.json();
    },

    // --- Personal GDrive ---
    async updateMyGDrive(token: string, data: { gdrive_creds?: string, gdrive_folder?: string }) {
        const res = await fetch(`${API_URL}/auth/me/gdrive`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('Failed to update Google Drive settings');
        return res.json();
    }

};
