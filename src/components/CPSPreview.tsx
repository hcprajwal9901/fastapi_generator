"use client";

import { useState, useEffect } from "react";
import { Copy, Check, AlertTriangle, DollarSign, FileCode, Activity } from "lucide-react";

interface CPSPreviewProps {
    cps: any;
    setCps: (cps: any) => void;
    onGenerate: () => void;
    loading: boolean;
}

export default function CPSPreview({ cps, setCps, onGenerate, loading }: CPSPreviewProps) {
    const [activeTab, setActiveTab] = useState<"json" | "config" | "analysis" | "openapi">("config");
    const [costs, setCosts] = useState<any>(null);
    const [validation, setValidation] = useState<any>(null);
    const [openapi, setOpenapi] = useState<any>(null);
    const [analyzing, setAnalyzing] = useState(false);

    // Auto-validate when CPS changes
    useEffect(() => {
        if (cps) {
            runValidation();
        }
    }, [cps]);

    const runValidation = async () => {
        try {
            const res = await fetch("/api/preflight", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ cps }),
            });
            const data = await res.json();
            setValidation(data);
        } catch (e) {
            console.error(e);
        }
    };

    const runAnalysis = async () => {
        setAnalyzing(true);
        try {
            // Cost Estimation
            const costRes = await fetch("/api/estimate-costs", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(cps),
            });
            setCosts(await costRes.json());

            // OpenAPI Preview
            if (cps.generation_options?.openapi_first) {
                const openapiRes = await fetch("/api/openapi-preview", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(cps),
                });
                setOpenapi(await openapiRes.json());
            }
        } catch (e) {
            console.error(e);
        } finally {
            setAnalyzing(false);
        }
    };

    const updateNested = (path: string[], value: any) => {
        const newCps = { ...cps };
        let current = newCps;
        for (let i = 0; i < path.length - 1; i++) {
            if (!current[path[i]]) current[path[i]] = {};
            current = current[path[i]];
        }
        current[path[path.length - 1]] = value;
        setCps(newCps);
    };

    if (!cps) {
        return (
            <div className="glass p-6 rounded-xl h-64 flex items-center justify-center text-white/40 italic">
                Extract a specification first...
            </div>
        );
    }

    return (
        <div className="glass p-6 rounded-xl space-y-4 flex flex-col h-full overflow-hidden">
            {/* Tabs */}
            <div className="flex gap-2 border-b border-white/10 pb-2 overflow-x-auto">
                <button
                    onClick={() => setActiveTab("config")}
                    className={`px-3 py-1.5 rounded text-sm flex items-center gap-2 transition ${activeTab === "config" ? "bg-white/10 text-white" : "hover:bg-white/5 text-white/60"}`}
                >
                    <Activity size={14} /> Config
                </button>
                <button
                    onClick={() => setActiveTab("json")}
                    className={`px-3 py-1.5 rounded text-sm flex items-center gap-2 transition ${activeTab === "json" ? "bg-white/10 text-white" : "hover:bg-white/5 text-white/60"}`}
                >
                    <FileCode size={14} /> JSON
                </button>
                <button
                    onClick={() => { setActiveTab("analysis"); runAnalysis(); }}
                    className={`px-3 py-1.5 rounded text-sm flex items-center gap-2 transition ${activeTab === "analysis" ? "bg-white/10 text-white" : "hover:bg-white/5 text-white/60"}`}
                >
                    <DollarSign size={14} /> Analysis
                </button>
                {cps.generation_options?.openapi_first && (
                    <button
                        onClick={() => { setActiveTab("openapi"); runAnalysis(); }}
                        className={`px-3 py-1.5 rounded text-sm flex items-center gap-2 transition ${activeTab === "openapi" ? "bg-white/10 text-white" : "hover:bg-white/5 text-white/60"}`}
                    >
                        <FileCode size={14} /> OpenAPI
                    </button>
                )}
            </div>

            {/* Validation Banner */}
            {validation && !validation.valid && (
                <div className="bg-red-500/10 border border-red-500/50 p-3 rounded text-xs space-y-1">
                    <div className="flex items-center gap-2 font-bold text-red-400">
                        <AlertTriangle size={14} /> Validation Errors
                    </div>
                    {validation.errors.map((e: any, i: number) => (
                        <div key={i} className="text-red-300">• {e.message}</div>
                    ))}
                </div>
            )}

            {/* Content Area */}
            <div className="flex-1 overflow-auto min-h-[300px]">
                {activeTab === "json" && (
                    <pre className="bg-black/40 p-4 rounded border border-white/10 text-xs font-mono h-full overflow-auto text-green-400">
                        {JSON.stringify(cps, null, 2)}
                    </pre>
                )}

                {activeTab === "config" && (
                    <div className="space-y-6 p-1">
                        {/* Provider Config */}
                        <div className="space-y-2">
                            <label className="text-xs font-bold text-white/60 uppercase tracking-wider">LLM Provider</label>
                            <select
                                value={typeof cps.llm_provider === 'string' ? cps.llm_provider : cps.llm_provider.type}
                                onChange={(e) => updateNested(['llm_provider', 'type'], e.target.value)}
                                className="w-full bg-black/20 border border-white/10 rounded p-2 text-sm focus:border-blue-500 outline-none"
                            >
                                <option value="openai">OpenAI (Default)</option>
                                <option value="azure_openai">Azure OpenAI</option>
                                <option value="local">Local (Skeleton)</option>
                            </select>
                        </div>

                        {/* Environment Config */}
                        <div className="space-y-4 border-t border-white/10 pt-4">
                            <label className="text-xs font-bold text-white/60 uppercase tracking-wider">Environment</label>
                            <div className="grid grid-cols-2 gap-4">
                                <label className="flex items-center gap-2 text-sm cursor-pointer p-2 bg-white/5 rounded hover:bg-white/10">
                                    <input
                                        type="checkbox"
                                        checked={cps.environment?.generate_dockerfile || false}
                                        onChange={(e) => updateNested(['environment', 'generate_dockerfile'], e.target.checked)}
                                        className="rounded border-white/20 bg-black/20"
                                    />
                                    Generate Dockerfile
                                </label>
                                <label className="flex items-center gap-2 text-sm cursor-pointer p-2 bg-white/5 rounded hover:bg-white/10">
                                    <input
                                        type="checkbox"
                                        checked={cps.environment?.generate_compose || false}
                                        onChange={(e) => updateNested(['environment', 'generate_compose'], e.target.checked)}
                                        className="rounded border-white/20 bg-black/20"
                                    />
                                    Docker Compose
                                </label>
                            </div>
                        </div>

                        {/* Generation Options */}
                        <div className="space-y-4 border-t border-white/10 pt-4">
                            <label className="text-xs font-bold text-white/60 uppercase tracking-wider">Generation Options</label>
                            <div className="space-y-2">
                                <label className="flex items-center gap-2 text-sm cursor-pointer p-2 bg-white/5 rounded hover:bg-white/10">
                                    <input
                                        type="checkbox"
                                        checked={cps.generation_options?.openapi_first || false}
                                        onChange={(e) => updateNested(['generation_options', 'openapi_first'], e.target.checked)}
                                        className="rounded border-white/20 bg-black/20"
                                    />
                                    <div>
                                        <div className="font-semibold">Contract-First Mode</div>
                                        <div className="text-xs text-white/50">Generate OpenAPI spec before code</div>
                                    </div>
                                </label>
                                <label className="flex items-center gap-2 text-sm cursor-pointer p-2 bg-white/5 rounded hover:bg-white/10">
                                    <input
                                        type="checkbox"
                                        checked={cps.generation_options?.generate_tests || false}
                                        onChange={(e) => updateNested(['generation_options', 'generate_tests'], e.target.checked)}
                                        className="rounded border-white/20 bg-black/20"
                                    />
                                    <div>
                                        <div className="font-semibold">Generate Tests</div>
                                        <div className="text-xs text-white/50">Include basic test suite</div>
                                    </div>
                                </label>
                                <label className="flex items-center gap-2 text-sm cursor-pointer p-2 bg-white/5 rounded hover:bg-white/10">
                                    <input
                                        type="checkbox"
                                        checked={cps.generation_options?.failure_first || false}
                                        onChange={(e) => updateNested(['generation_options', 'failure_first'], e.target.checked)}
                                        className="rounded border-white/20 bg-black/20"
                                    />
                                    <div>
                                        <div className="font-semibold">Failure-First Design</div>
                                        <div className="text-xs text-white/50">Stub incomplete features with errors</div>
                                    </div>
                                </label>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === "analysis" && (
                    <div className="space-y-6 p-1">
                        {analyzing ? (
                            <div className="flex items-center justify-center h-32 text-white/40 animate-pulse">Running analysis...</div>
                        ) : costs ? (
                            <>
                                {/* Cost Estimates */}
                                <div className="space-y-2">
                                    <h3 className="text-sm font-bold text-green-400 flex items-center gap-2">
                                        <DollarSign size={16} /> Estimated Costs
                                    </h3>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="bg-white/5 p-3 rounded">
                                            <div className="text-xs text-white/50">Input Cost / 1k Tokens</div>
                                            <div className="text-lg font-mono">${costs.costs_usd?.per_chat_request || 0}</div>
                                        </div>
                                        <div className="bg-white/5 p-3 rounded">
                                            <div className="text-xs text-white/50">Output Cost / 1k Tokens</div>
                                            <div className="text-lg font-mono">${costs.costs_usd?.per_rag_query || 0}</div>
                                        </div>
                                    </div>
                                    <div className="text-[10px] text-white/30 italic mt-2 border-t border-white/10 pt-2">
                                        {costs.disclaimer}
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="text-center text-white/40">Click tab to load analysis</div>
                        )}
                    </div>
                )}

                {activeTab === "openapi" && (
                    <div className="h-full">
                        {analyzing ? (
                            <div className="flex items-center justify-center h-32 text-white/40 animate-pulse">Generating Spec...</div>
                        ) : openapi ? (
                            <pre className="bg-black/40 p-4 rounded border border-white/10 text-xs font-mono h-full overflow-auto text-blue-400">
                                {JSON.stringify(openapi.json, null, 2)}
                            </pre>
                        ) : (
                            <div className="text-center text-white/40">No OpenAPI spec generated</div>
                        )}
                    </div>
                )}
            </div>

            <button
                onClick={onGenerate}
                disabled={loading || (validation && !validation.valid)}
                className="w-full py-4 bg-gradient-to-r from-blue-600 to-blue-500 disabled:from-gray-700 disabled:to-gray-800 rounded-lg font-bold hover:shadow-lg hover:shadow-blue-500/20 transition flex items-center justify-center gap-2"
            >
                {loading ? "Generating..." : "Generate Project"}
            </button>
        </div>
    );
}
