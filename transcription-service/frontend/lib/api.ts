const API_URL = "http://localhost:8000";

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

    async register(email: string, password: string) {
        const res = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });

        if (!res.ok) {
            throw new Error('Registration failed');
        }
        return res.json();
    },

    async getTranscripts(token: string) {
        const res = await fetch(`${API_URL}/transcripts/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return res.json();
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
    }
};
