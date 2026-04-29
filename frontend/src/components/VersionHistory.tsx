'use client';

import { useState } from 'react';
import type { LessonPlan } from './LessonPlanEditor';

interface LessonVersion {
  version: number;
  lesson: LessonPlan;
  createdAt: string;
  description?: string;
}

interface VersionHistoryProps {
  versions: LessonVersion[];
  currentVersion: number;
  onRestore: (version: number) => void;
  maxVersions?: number;
}

export function VersionHistory({
  versions,
  currentVersion,
  onRestore,
  maxVersions = 3,
}: VersionHistoryProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (versions.length === 0) return null;

  // Sort versions descending (newest first)
  const sortedVersions = [...versions].sort((a, b) => b.version - a.version);

  return (
    <div className="w-full">
      {/* Toggle button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800"
      >
        <svg
          className={`w-4 h-4 transform transition-transform ${isExpanded ? 'rotate-90' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        <span>版本历史 ({versions.length}/{maxVersions})</span>
      </button>

      {/* Version list */}
      {isExpanded && (
        <div className="mt-2 space-y-2">
          {sortedVersions.map((v) => (
            <div
              key={v.version}
              className={`flex items-center gap-3 rounded border p-2 ${
                v.version === currentVersion
                  ? 'border-blue-300 bg-blue-50'
                  : 'border-gray-200 bg-gray-50'
              }`}
            >
              {/* Version indicator */}
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  v.version === currentVersion
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-300 text-gray-600'
                }`}
              >
                v{v.version}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">
                  {v.lesson.meta.title || '未命名教案'}
                </div>
                <div className="text-xs text-gray-500">
                  {new Date(v.createdAt).toLocaleString('zh-CN')}
                  {v.description && ` - ${v.description}`}
                </div>
              </div>

              {/* Restore button */}
              {v.version !== currentVersion && (
                <button
                  onClick={() => onRestore(v.version)}
                  className="text-xs text-blue-600 hover:text-blue-700 px-2 py-1"
                >
                  恢复
                </button>
              )}

              {/* Current indicator */}
              {v.version === currentVersion && (
                <span className="text-xs text-blue-600 font-medium">当前</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}