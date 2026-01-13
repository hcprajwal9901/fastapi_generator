"""
Diff Engine - Feature #10: Diff-Aware Regeneration

Shows file-level diffs when a project is regenerated.

Rules:
- Diff must be deterministic
- No auto-merging without user confirmation
- Unchanged files are preserved
- All comparisons are explicit
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from difflib import unified_diff, SequenceMatcher


class FileStatus(Enum):
    """Status of a file in the diff"""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class FileDiff:
    """
    Represents a file difference between old and new versions.
    
    Provides detailed diff information for user review.
    """
    path: str
    status: FileStatus
    diff_lines: List[str]  # Unified diff format
    additions: int = 0     # Number of added lines
    deletions: int = 0     # Number of deleted lines
    similarity: float = 1.0  # 0.0 to 1.0, how similar the files are
    
    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "status": self.status.value,
            "diff": "".join(self.diff_lines),
            "additions": self.additions,
            "deletions": self.deletions,
            "similarity": round(self.similarity, 2),
        }


@dataclass
class DiffResult:
    """
    Complete diff result for all files.
    
    Summarizes changes and provides per-file diffs.
    """
    files: List[FileDiff]
    
    @property
    def added_count(self) -> int:
        return sum(1 for f in self.files if f.status == FileStatus.ADDED)
    
    @property
    def removed_count(self) -> int:
        return sum(1 for f in self.files if f.status == FileStatus.REMOVED)
    
    @property
    def modified_count(self) -> int:
        return sum(1 for f in self.files if f.status == FileStatus.MODIFIED)
    
    @property
    def unchanged_count(self) -> int:
        return sum(1 for f in self.files if f.status == FileStatus.UNCHANGED)
    
    def to_dict(self) -> Dict:
        return {
            "summary": {
                "added": self.added_count,
                "removed": self.removed_count,
                "modified": self.modified_count,
                "unchanged": self.unchanged_count,
                "total": len(self.files),
            },
            "files": [f.to_dict() for f in self.files],
        }
    
    def get_changed_files(self) -> List[FileDiff]:
        """Get only files that changed (added, removed, or modified)"""
        return [
            f for f in self.files
            if f.status != FileStatus.UNCHANGED
        ]


def compute_diff(
    old_files: Dict[str, str],
    new_files: Dict[str, str]
) -> DiffResult:
    """
    Compute deterministic file-level diffs between two file sets.
    
    This comparison is:
    - Deterministic: Same inputs always produce same outputs
    - Complete: All files are compared
    - User-controlled: No auto-merging
    
    Args:
        old_files: Dictionary of path -> content for old version
        new_files: Dictionary of path -> content for new version
        
    Returns:
        DiffResult with all file diffs
    """
    diffs: List[FileDiff] = []
    
    # Get all unique paths
    all_paths = set(old_files.keys()) | set(new_files.keys())
    
    for path in sorted(all_paths):
        old_content = old_files.get(path, "")
        new_content = new_files.get(path, "")
        
        if path not in old_files:
            # New file added
            diffs.append(FileDiff(
                path=path,
                status=FileStatus.ADDED,
                diff_lines=_generate_add_diff(path, new_content),
                additions=new_content.count("\n") + 1 if new_content else 0,
                deletions=0,
                similarity=0.0,
            ))
        
        elif path not in new_files:
            # File removed
            diffs.append(FileDiff(
                path=path,
                status=FileStatus.REMOVED,
                diff_lines=_generate_remove_diff(path, old_content),
                additions=0,
                deletions=old_content.count("\n") + 1 if old_content else 0,
                similarity=0.0,
            ))
        
        elif old_content != new_content:
            # File modified
            diff_lines = list(unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
                lineterm=""
            ))
            
            additions = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
            deletions = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))
            
            # Calculate similarity
            similarity = SequenceMatcher(None, old_content, new_content).ratio()
            
            diffs.append(FileDiff(
                path=path,
                status=FileStatus.MODIFIED,
                diff_lines=diff_lines,
                additions=additions,
                deletions=deletions,
                similarity=similarity,
            ))
        
        else:
            # File unchanged
            diffs.append(FileDiff(
                path=path,
                status=FileStatus.UNCHANGED,
                diff_lines=[],
                additions=0,
                deletions=0,
                similarity=1.0,
            ))
    
    return DiffResult(files=diffs)


def _generate_add_diff(path: str, content: str) -> List[str]:
    """Generate diff lines for a newly added file"""
    lines = [
        f"--- /dev/null\n",
        f"+++ b/{path}\n",
        f"@@ -0,0 +1,{content.count(chr(10)) + 1} @@\n",
    ]
    for line in content.splitlines():
        lines.append(f"+{line}\n")
    return lines


def _generate_remove_diff(path: str, content: str) -> List[str]:
    """Generate diff lines for a removed file"""
    lines = [
        f"--- a/{path}\n",
        f"+++ /dev/null\n",
        f"@@ -1,{content.count(chr(10)) + 1} +0,0 @@\n",
    ]
    for line in content.splitlines():
        lines.append(f"-{line}\n")
    return lines


def apply_selective_merge(
    old_files: Dict[str, str],
    new_files: Dict[str, str],
    paths_to_update: List[str]
) -> Dict[str, str]:
    """
    Apply selective merge based on user-selected paths.
    
    This allows users to choose which files to update during regeneration.
    
    Args:
        old_files: Original file set
        new_files: Newly generated file set
        paths_to_update: List of paths the user wants to update
        
    Returns:
        Merged file set
    """
    result = old_files.copy()
    
    for path in paths_to_update:
        if path in new_files:
            result[path] = new_files[path]
        elif path in result:
            # User selected a file that was removed in new version
            del result[path]
    
    # Add any new files that were selected
    for path in paths_to_update:
        if path in new_files and path not in old_files:
            result[path] = new_files[path]
    
    return result
