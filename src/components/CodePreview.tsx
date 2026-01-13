"use client";

import { useState, useMemo } from "react";
import dynamic from "next/dynamic";
import { Folder, FileCode, GitCommit, Code2, ChevronRight, ChevronDown } from "lucide-react";

const Editor = dynamic(() => import("@monaco-editor/react"), { ssr: false });
const DiffEditor = dynamic(() => import("@monaco-editor/react").then(mod => mod.DiffEditor), { ssr: false });

interface CodePreviewProps {
    files: Record<string, string>;
    oldFiles?: Record<string, string>;
    diff?: any;
    onUpdateFile: (path: string, content: string) => void;
}

type FileNode = {
    name: string;
    path: string;
    type: 'file' | 'folder';
    children?: FileNode[];
};

const buildTree = (paths: string[]): FileNode[] => {
    const root: FileNode[] = [];

    // Helper to find or create node in list
    const findOrCreate = (list: FileNode[], name: string, path: string, type: 'file' | 'folder'): FileNode => {
        let node = list.find(n => n.name === name);
        if (!node) {
            node = { name, path, type, children: [] };
            list.push(node);
        }
        return node;
    };

    paths.forEach(filepath => {
        const parts = filepath.split('/');
        let currentLevel = root;

        parts.forEach((part, index) => {
            const isFile = index === parts.length - 1;
            const path = parts.slice(0, index + 1).join('/');

            // Only add node if it doesn't exist at this level
            const node = findOrCreate(currentLevel, part, path, isFile ? 'file' : 'folder');

            if (!isFile) {
                // If it's a folder, traverse into its children
                if (!node.children) node.children = [];
                currentLevel = node.children;
            }
        });
    });

    // Recursive sort: folders first, then files alphabetically
    const sortTree = (nodes: FileNode[]): FileNode[] => {
        return nodes.sort((a, b) => {
            if (a.type === b.type) return a.name.localeCompare(b.name);
            return a.type === 'folder' ? -1 : 1;
        }).map(n => ({
            ...n,
            children: n.children ? sortTree(n.children) : undefined
        }));
    }

    return sortTree(root);
};

const FileTreeItem = ({ node, selectedPath, onSelect, getStatusColor, depth = 0 }: any) => {
    const [expanded, setExpanded] = useState(true);
    const isSelected = selectedPath === node.path;
    const paddingLeft = `${depth * 12 + 12}px`;

    if (node.type === 'folder') {
        return (
            <div>
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="w-full text-left py-1.5 flex items-center hover:bg-white/5 text-white/60 text-xs font-medium transition-colors"
                    style={{ paddingLeft }}
                >
                    <span className="mr-1.5 opacity-60">
                        {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    </span>
                    <Folder size={14} className="mr-2 text-blue-400/70" />
                    <span className="truncate">{node.name}</span>
                </button>
                {expanded && node.children && (
                    <div>
                        {node.children.map((child: any) => (
                            <FileTreeItem
                                key={child.path}
                                node={child}
                                selectedPath={selectedPath}
                                onSelect={onSelect}
                                getStatusColor={getStatusColor}
                                depth={depth + 1}
                            />
                        ))}
                    </div>
                )}
            </div>
        );
    }

    return (
        <button
            onClick={() => onSelect(node.path)}
            className={`w-full text-left py-1.5 flex items-center text-xs transition-colors ${isSelected ? 'bg-blue-500/10 text-blue-400 border-r-2 border-blue-500' : 'hover:bg-white/5 text-white/70'
                }`}
            style={{ paddingLeft: `${depth * 12 + 28}px` }}
        >
            <FileCode size={13} className={`mr-2 ${getStatusColor(node.path)}`} />
            <span className={`truncate ${getStatusColor(node.path)}`}>{node.name}</span>
        </button>
    );
};

export default function CodePreview({ files, oldFiles, diff, onUpdateFile }: CodePreviewProps) {
    const [selectedPath, setSelectedPath] = useState<string | null>(null);
    const [viewMode, setViewMode] = useState<"code" | "diff">("code");

    // Initialize selected path if needed
    useMemo(() => {
        if (!selectedPath && Object.keys(files).length > 0) {
            const candidates = Object.keys(files);
            const preferred = candidates.find(p => p.endsWith('README.md')) || candidates.find(p => p.endsWith('main.py')) || candidates[0];
            setSelectedPath(preferred);
        }
    }, [files, selectedPath]);

    const allPaths = useMemo(() => {
        const paths = new Set(Object.keys(files));
        if (diff) {
            diff.files.forEach((f: any) => paths.add(f.path));
        }
        return Array.from(paths);
    }, [files, diff]);

    const fileTree = useMemo(() => buildTree(allPaths), [allPaths]);

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
        return "";
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
                <div className="text-xs text-white/40 font-mono truncate max-w-[400px]">{currentPath}</div>
            </div>

            <div className="flex-1 flex overflow-hidden">
                {/* Sidebar */}
                <div className="w-64 border-r border-white/10 bg-black/20 flex flex-col">
                    <div className="p-3 uppercase text-[10px] font-bold text-white/40 tracking-widest flex justify-between items-center border-b border-white/5">
                        <span>Explorer</span>
                        {diff && <span className="text-[10px] bg-white/10 px-1.5 py-0.5 rounded text-white/60">{diff.summary.modified}M {diff.summary.added}A</span>}
                    </div>
                    <div className="flex-1 overflow-y-auto p-1 custom-scrollbar">
                        {fileTree.map(node => (
                            <FileTreeItem
                                key={node.path}
                                node={node}
                                selectedPath={currentPath}
                                onSelect={setSelectedPath}
                                getStatusColor={getStatusColor}
                            />
                        ))}
                    </div>
                </div>

                {/* Editor Area */}
                <div className="flex-1 bg-[#1e1e1e] relative flex flex-col">
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
                                lineNumbers: "on",
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
