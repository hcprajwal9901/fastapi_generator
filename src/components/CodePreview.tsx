"use client";

import { useState, useMemo } from "react";
import dynamic from "next/dynamic";
import { Folder, FileCode, GitCommit, Eye, Code2 } from "lucide-react";

const Editor = dynamic(() => import("@monaco-editor/react"), { ssr: false });
const DiffEditor = dynamic(() => import("@monaco-editor/react").then(mod => mod.DiffEditor), { ssr: false });

interface CodePreviewProps {
    files: Record<string, string>;
    oldFiles?: Record<string, string>;
    diff?: any;
    onUpdateFile: (path: string, content: string) => void;
}

export default function CodePreview({ files, oldFiles, diff, onUpdateFile }: CodePreviewProps) {
    const [selectedPath, setSelectedPath] = useState<string | null>(null);
    const [viewMode, setViewMode] = useState<"code" | "diff">("code");

    // Initialize selected path if needed
    if (!selectedPath && Object.keys(files).length > 0) {
        setSelectedPath(Object.keys(files)[0]);
    }

    const paths = Object.keys(files).sort();

    // Determine file status from diff items
    const fileStatus = useMemo(() => {
        if (!diff) return {};
        const status: Record<string, string> = {};
        diff.files.forEach((f: any) => {
            status[f.path] = f.status;
        });
        return status;
    }, [diff]);

    const getStatusColor = (path: string) => {
        const status = fileStatus[path];
        if (status === "added") return "text-green-400";
        if (status === "modified") return "text-yellow-400";
        if (status === "removed") return "text-red-400 decoration-line-through";
        return "text-white/70";
    };

    const currentPath = selectedPath || "";
    const originalContent = oldFiles ? oldFiles[currentPath] || "" : "";
    const modifiedContent = files[currentPath] || "";

    return (
        <div className="flex-1 flex flex-col border border-white/10 rounded-xl overflow-hidden glass h-[600px]">
            {/* Toolbar */}
            <div className="bg-black/20 border-b border-white/10 p-2 flex justify-between items-center">
                <div className="flex gap-2">
                    <button
                        onClick={() => setViewMode("code")}
                        className={`px-3 py-1.5 rounded text-xs flex items-center gap-2 transition ${viewMode === "code" ? "bg-blue-600 text-white" : "hover:bg-white/5 text-white/60"}`}
                    >
                        <Code2 size={14} /> Code
                    </button>
                    {oldFiles && (
                        <button
                            onClick={() => setViewMode("diff")}
                            className={`px-3 py-1.5 rounded text-xs flex items-center gap-2 transition ${viewMode === "diff" ? "bg-blue-600 text-white" : "hover:bg-white/5 text-white/60"}`}
                        >
                            <GitCommit size={14} /> Diff
                        </button>
                    )}
                </div>
                <div className="text-xs text-white/40 font-mono">{currentPath}</div>
            </div>

            <div className="flex-1 flex overflow-hidden">
                {/* Sidebar */}
                <div className="w-64 border-r border-white/10 bg-black/20 overflow-y-auto">
                    <div className="p-4 uppercase text-xs font-bold text-white/40 tracking-widest flex justify-between items-center">
                        Files
                        {diff && <span className="text-[10px] bg-white/10 px-2 py-0.5 rounded text-white/60">{diff.summary.modified} mod, {diff.summary.added} add</span>}
                    </div>
                    <div className="space-y-0.5 p-2">
                        {paths.map(path => (
                            <button
                                key={path}
                                onClick={() => setSelectedPath(path)}
                                className={`w-full text-left px-3 py-2 rounded text-xs flex items-center space-x-2 transition ${selectedPath === path ? "bg-white/5 text-white" : "hover:bg-white/5"
                                    }`}
                            >
                                <FileCode className={`w-3.5 h-3.5 ${getStatusColor(path)}`} />
                                <span className={`truncate ${getStatusColor(path)}`}>{path.split("/").pop()}</span>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Editor Area */}
                <div className="flex-1 bg-[#1e1e1e] relative">
                    {viewMode === "diff" && oldFiles ? (
                        <DiffEditor
                            height="100%"
                            theme="vs-dark"
                            original={originalContent}
                            modified={modifiedContent}
                            language="python"
                            options={{
                                readOnly: true,
                                minimap: { enabled: false },
                                fontSize: 13,
                            }}
                        />
                    ) : (
                        <Editor
                            height="100%"
                            theme="vs-dark"
                            path={currentPath}
                            defaultLanguage="python"
                            value={modifiedContent}
                            onChange={(val) => currentPath && onUpdateFile(currentPath, val || "")}
                            options={{
                                minimap: { enabled: false },
                                fontSize: 13,
                                padding: { top: 16 }
                            }}
                        />
                    )}
                </div>
            </div>
        </div>
    );
}
