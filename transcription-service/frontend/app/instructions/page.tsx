"use client";
import React from 'react';
import { useRouter } from 'next/navigation';

export default function Instructions() {
    const router = useRouter();

    return (
        <main className="min-h-screen p-8 bg-[#0a0c10] text-[#c9d1d9]">
            <div className="max-w-4xl mx-auto">
                <button
                    onClick={() => router.push('/dashboard')}
                    className="text-xs text-slate-500 hover:text-white mb-8 flex items-center gap-1"
                >
                    ← BACK TO WORKSPACE
                </button>

                <h1 className="text-4xl font-extrabold tracking-tight text-white mb-4">Integration Guide</h1>
                <p className="text-slate-400 mb-12 border-b border-[#30363d] pb-8">Follow these steps to connect your external tools and storage.</p>

                <section className="mb-16">
                    <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                        <span className="w-8 h-8 rounded-full bg-blue-500/10 text-blue-500 flex items-center justify-center text-sm">1</span>
                        Google Drive Export
                    </h2>
                    <div className="space-y-4 text-slate-300 ml-11">
                        <p>To enable automatic export of your transcripts, you need a Google Service Account.</p>
                        <ol className="list-decimal list-inside space-y-3">
                            <li>Go to <a href="https://console.cloud.google.com/" target="_blank" className="text-blue-400 hover:underline">Google Cloud Console</a>.</li>
                            <li>Create a project and enable the <b>Google Drive API</b>.</li>
                            <li>In <b>Credentials</b>, create a <b>Service Account</b>.</li>
                            <li>Generate a <b>JSON Key</b> and save it.</li>
                            <li>Share your target Drive Folder with the Service Account email.</li>
                            <li>Paste the JSON content and Folder ID into your Project/Profile settings.</li>
                        </ol>
                    </div>
                </section>

                <section className="mb-16">
                    <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                        <span className="w-8 h-8 rounded-full bg-green-500/10 text-green-500 flex items-center justify-center text-sm">2</span>
                        CLI & IDE Plugin
                    </h2>
                    <div className="space-y-4 text-slate-300 ml-11">
                        <p>Interact with the service directly from your terminal or IDE.</p>
                        <div className="bg-[#0d1117] p-4 rounded border border-[#30363d] font-mono text-sm overflow-x-auto">
                            <code>
                                # Set your API Key<br />
                                export TRANSCRIPTION_API_KEY="your_key_here"<br /><br />
                                # List your transcripts<br />
                                python scripts/ide_plugin.py list<br /><br />
                                # Upload a local file<br />
                                python scripts/ide_plugin.py upload ./meeting.mp3
                            </code>
                        </div>
                        <p className="text-sm text-slate-500 mt-4">
                            You can find your API key on the Dashboard.
                        </p>
                    </div>
                </section>

                <footer className="py-12 border-t border-[#30363d] text-center text-slate-500 text-sm">
                    Transcription Service Integration Docs • 2024
                </footer>
            </div>
        </main>
    );
}
