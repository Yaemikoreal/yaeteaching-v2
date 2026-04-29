'use client';

import type { ChangedSections } from './LessonPlanEditor';

interface ChangeIndicatorProps {
  changes: ChangedSections;
}

export function ChangeIndicator({ changes }: ChangeIndicatorProps) {
  const changedCount =
    (changes.meta ? 1 : 0) +
    changes.sections.size +
    (changes.summary ? 1 : 0);

  if (changedCount === 0) return null;

  return (
    <div className="flex items-center gap-2 rounded bg-yellow-50 px-3 py-2 border border-yellow-200">
      <div className="w-4 h-4 rounded bg-yellow-400 flex items-center justify-center">
        <span className="text-white text-xs font-bold">{changedCount}</span>
      </div>
      <div className="text-sm">
        <span className="text-yellow-700 font-medium">修改内容：</span>
        <span className="text-yellow-600">
          {changes.meta && '基本信息'}
          {changes.meta && (changes.sections.size > 0 || changes.summary) && '、'}
          {changes.sections.size > 0 && `${changes.sections.size}个章节`}
          {changes.sections.size > 0 && changes.summary && '、'}
          {changes.summary && '总结'}
        </span>
      </div>
      <div className="ml-auto text-xs text-yellow-500">
        仅重新生成修改过的部分
      </div>
    </div>
  );
}