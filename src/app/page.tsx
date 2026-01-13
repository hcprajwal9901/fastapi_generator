"use client";

import { useState } from "react";
import ProjectInput from "@/components/ProjectInput";
import CPSPreview from "@/components/CPSPreview";
import CodePreview from "@/components/CodePreview";
import Header from "@/components/Header";

export default function Home() {
    const [cps, setCps] = useState<any>(null);
    const [files, setFiles] = useState<Record<string, string>>({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [mode, setMode] = useState<"general" | "rag_only">("general");
    const [feedback, setFeedback] = useState("");

    const handleAnalyze = async (text: string) => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: `Mode: ${mode}. ${text}` }),
            });
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            setCps(data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const [oldFiles, setOldFiles] = useState<Record<string, string> | null>(null);
    const [diff, setDiff] = useState<any>(null);

    const handleGenerate = async () => {
        setLoading(true);
        setError(null);
        setDiff(null);
        try {
            // Determine if we should generate or regenerate
            const endpoint = oldFiles ? "/api/regenerate" : "/api/generate";
            const body = oldFiles ? { cps, old_files: oldFiles } : cps;

            const res = await fetch(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });
            const data = await res.json();

            if (data.detail) {
                setError(JSON.stringify(data.detail));
                return;
            }

            // Handle output format
            if (data.diff) {
                setFiles(data.files);
                setDiff(data.diff);
            } else {
                setFiles(data.files || data); // Handle both formats
            }
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleBack = () => {
        setOldFiles(files);
        setFiles({});
        setDiff(null);
    };

    const handleRefine = async () => {
        if (!feedback) return;
        setLoading(true);
        setError(null);
        try {
            const res = await fetch("/api/refine", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ cps, files, feedback }),
            });
            const data = await res.json();
            if (data.error) throw new Error(data.error);

            // If refining, we treat the previous files as 'old' for potential diffing logic later
            // But usually refine just updates in place. 
            // We could optionally compute diff here too if we wanted.
            setFiles(data.files);
            setFeedback("");
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = async () => {
        try {
            const res = await fetch("/api/export", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ files }),
            });
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "project.zip";
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (err: any) {
            setError("Export failed: " + err.message);
        }
    };

    return (
        <main className="min-h-screen p-4 md:p-8 space-y-8 max-w-7xl mx-auto">
            <Header />

            {!files || Object.keys(files).length === 0 ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <section className="space-y-4">
                        <div className="flex justify-between items-center">
                            <h2 className="text-2xl font-bold">1. Project Idea</h2>
                            <div className="flex bg-white/5 rounded-lg p-1 border border-white/10">
                                <button
                                    onClick={() => setMode("general")}
                                    className={`px-3 py-1 rounded text-xs transition ${mode === "general" ? "bg-blue-600 text-white" : "hover:text-white"}`}
                                >
                                    General
                                </button>
                                <button
                                    onClick={() => setMode("rag_only")}
                                    className={`px-3 py-1 rounded text-xs transition ${mode === "rag_only" ? "bg-blue-600 text-white" : "hover:text-white"}`}
                                >
                                    RAG-Only
                                </button>
                            </div>
                        </div>
                        <ProjectInput onAnalyze={handleAnalyze} loading={loading} />
                        {error && <div className="p-4 bg-red-900/20 border border-red-500 rounded text-red-500">{error}</div>}
                    </section>

                    <section className="space-y-4">
                        <h2 className="text-2xl font-bold">2. Review Specification (CPS)</h2>
                        <CPSPreview cps={cps} setCps={setCps} onGenerate={handleGenerate} loading={loading} />
                    </section>
                </div>
            ) : (
                <section className="space-y-4 h-[calc(100vh-200px)] flex flex-col">
                    <div className="flex justify-between items-center">
                        <h2 className="text-2xl font-bold">3. Generated Code</h2>
                        <div className="space-x-4">
                            <button
                                onClick={handleBack}
                                className="px-4 py-2 border border-foreground/20 rounded hover:bg-foreground/10 transition"
                            >
                                Back
                            </button>
                            <button
                                onClick={handleDownload}
                                className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700 transition font-bold"
                            >
                                Download ZIP
                            </button>
                        </div>
                    </div>
                    <CodePreview
                        files={files}
                        oldFiles={oldFiles || undefined}
                        diff={diff}
                        onUpdateFile={(path, content) => setFiles(prev => ({ ...prev, [path]: content }))}
                    />

                    <div className="p-4 bg-white/5 border border-white/10 rounded-lg space-y-4 shadow-xl backdrop-blur-md">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                            <h3 className="font-semibold text-blue-400">Review & Fix</h3>
                        </div>
                        <p className="text-xs text-foreground/60">Mention any bugs or features to add to the generated code.</p>
                        <div className="flex gap-4">
                            <textarea
                                value={feedback}
                                onChange={(e) => setFeedback(e.target.value)}
                                placeholder="e.g., Fix the bug in main.py or add a database session to the chat endpoint..."
                                className="flex-1 bg-black/40 border border-white/10 rounded-lg p-3 text-sm focus:ring-1 focus:ring-blue-500 outline-none min-h-[80px]"
                            />
                            <button
                                onClick={handleRefine}
                                disabled={loading || !feedback}
                                className="px-6 bg-blue-600 rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-bold"
                            >
                                {loading ? "Fixing..." : "Refine Code"}
                            </button>
                        </div>
                    </div>
                </section>
            )}
        </main>
    );
}
