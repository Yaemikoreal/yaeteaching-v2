'use client';

import { useState, useCallback } from 'react';
import { ChangeIndicator } from './ChangeIndicator';

// Lesson Plan types (matching backend schema)
export interface LessonPlan {
  meta: {
    topic: string;
    subject: string;
    grade: string;
    duration: number;
    style?: string;
  };
  outline: Array<{
    section_id: number;
    title: string;
    content: string;
    teaching_points: string[];
    examples: string[];
    media_hint?: {
      slide_type?: string;
      voice_style?: string;
      duration_hint?: number;
    };
  }>;
  summary: {
    key_points: string[];
    homework: string;
    next_preview: string;
    resources?: Array<{
      type: string;
      url?: string;
      description: string;
    }>;
  };
}

interface LessonPlanEditorProps {
  jobId: string;
  initialLesson: LessonPlan;
  onSave: (lesson: LessonPlan, changes: ChangedSections) => Promise<void>;
  onRegenerate: (sections: number[]) => Promise<void>;
}

// Track which sections have been modified
export interface ChangedSections {
  meta: boolean;
  sections: Set<number>;
  summary: boolean;
}

// Deep clone for comparison
function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

// Detect changes between original and edited lesson
function detectChanges(original: LessonPlan, edited: LessonPlan): ChangedSections {
  const changes: ChangedSections = {
    meta: false,
    sections: new Set(),
    summary: false,
  };

  // Check meta
  if (
    original.meta.topic !== edited.meta.topic ||
    original.meta.subject !== edited.meta.subject ||
    original.meta.grade !== edited.meta.grade ||
    original.meta.duration !== edited.meta.duration
  ) {
    changes.meta = true;
  }

  // Check sections
  original.outline.forEach((section, index) => {
    const editedSection = edited.outline[index];
    if (!editedSection) {
      changes.sections.add(section.section_id);
      return;
    }
    if (
      section.title !== editedSection.title ||
      section.content !== editedSection.content ||
      JSON.stringify(section.teaching_points) !== JSON.stringify(editedSection.teaching_points) ||
      JSON.stringify(section.examples) !== JSON.stringify(editedSection.examples)
    ) {
      changes.sections.add(section.section_id);
    }
  });

  // Check summary
  if (
    JSON.stringify(original.summary.key_points) !== JSON.stringify(edited.summary.key_points) ||
    original.summary.homework !== edited.summary.homework ||
    original.summary.next_preview !== edited.summary.next_preview
  ) {
    changes.summary = true;
  }

  return changes;
}

export function LessonPlanEditor({
  initialLesson,
  onSave,
  onRegenerate,
}: LessonPlanEditorProps) {
  const [lesson, setLesson] = useState<LessonPlan>(deepClone(initialLesson));
  const [originalLesson] = useState<LessonPlan>(deepClone(initialLesson));
  const [editMode, setEditMode] = useState<'structured' | 'json'>('structured');
  // Initialize JSON text from initial lesson (avoid setState in effect)
  const [jsonText, setJsonText] = useState<string>(() => JSON.stringify(initialLesson, null, 2));
  const [isSaving, setIsSaving] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [regenerateError, setRegenerateError] = useState<string | null>(null);

  // Track changes
  const changes = detectChanges(originalLesson, lesson);
  const hasChanges = changes.meta || changes.sections.size > 0 || changes.summary;

  // Update JSON text when switching to JSON mode (not in effect)
  const handleModeSwitch = useCallback((mode: 'structured' | 'json') => {
    if (mode === 'json') {
      setJsonText(JSON.stringify(lesson, null, 2));
    }
    setEditMode(mode);
  }, [lesson]);

  // Handle JSON edit
  const handleJsonEdit = useCallback((text: string) => {
    setJsonText(text);
    try {
      const parsed = JSON.parse(text) as LessonPlan;
      setLesson(parsed);
      setSaveError(null);
    } catch {
      // Invalid JSON, keep text but don't update lesson
      setSaveError('JSON 格式错误');
    }
  }, []);

  // Update section field
  const updateSection = useCallback((
    sectionId: number,
    field: 'title' | 'content',
    value: string
  ) => {
    setLesson(prev => ({
      ...prev,
      outline: prev.outline.map(section =>
        section.section_id === sectionId
          ? { ...section, [field]: value }
          : section
      ),
    }));
  }, []);

  // Update teaching points for a section
  const updateTeachingPoints = useCallback((
    sectionId: number,
    points: string[]
  ) => {
    setLesson(prev => ({
      ...prev,
      outline: prev.outline.map(section =>
        section.section_id === sectionId
          ? { ...section, teaching_points: points }
          : section
      ),
    }));
  }, []);

  // Update examples for a section
  const updateExamples = useCallback((
    sectionId: number,
    examples: string[]
  ) => {
    setLesson(prev => ({
      ...prev,
      outline: prev.outline.map(section =>
        section.section_id === sectionId
          ? { ...section, examples }
          : section
      ),
    }));
  }, []);

  // Update summary
  const updateSummary = useCallback((
    field: 'key_points' | 'homework' | 'next_preview',
    value: string | string[]
  ) => {
    setLesson(prev => ({
      ...prev,
      summary: {
        ...prev.summary,
        [field]: value,
      },
    }));
  }, []);

  // Update meta
  const updateMeta = useCallback((
    field: 'topic' | 'subject' | 'grade' | 'duration',
    value: string | number
  ) => {
    setLesson(prev => ({
      ...prev,
      meta: {
        ...prev.meta,
        [field]: value,
      },
    }));
  }, []);

  // Save lesson
  const handleSave = useCallback(async () => {
    if (!hasChanges) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      await onSave(lesson, changes);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : '保存失败');
    } finally {
      setIsSaving(false);
    }
  }, [lesson, changes, hasChanges, onSave]);

  // Regenerate modified sections
  const handleRegenerate = useCallback(async () => {
    const sectionIds = Array.from(changes.sections);
    if (sectionIds.length === 0) return;
    setIsRegenerating(true);
    setRegenerateError(null);
    try {
      await onRegenerate(sectionIds);
    } catch (err) {
      setRegenerateError(err instanceof Error ? err.message : '重新生成失败');
    } finally {
      setIsRegenerating(false);
    }
  }, [changes.sections, onRegenerate]);

  return (
    <div className="w-full space-y-4">
      {/* Header with mode toggle */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">教案编辑</h2>
        <div className="flex gap-2">
          <button
            onClick={() => handleModeSwitch('structured')}
            className={`px-3 py-1 rounded text-sm ${
              editMode === 'structured'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            结构化
          </button>
          <button
            onClick={() => handleModeSwitch('json')}
            className={`px-3 py-1 rounded text-sm ${
              editMode === 'json'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            JSON
          </button>
        </div>
      </div>

      {/* Changes indicator */}
      {hasChanges && (
        <ChangeIndicator changes={changes} />
      )}

      {/* Error messages */}
      {saveError && (
        <div className="rounded bg-red-50 p-3 text-sm text-red-600">
          {saveError}
        </div>
      )}
      {regenerateError && (
        <div className="rounded bg-red-50 p-3 text-sm text-red-600">
          {regenerateError}
        </div>
      )}

      {/* Editor content */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        {editMode === 'structured' ? (
          <div className="space-y-4">
            {/* Meta section */}
            <div className={`border-b pb-4 ${changes.meta ? 'bg-yellow-50 -mx-4 px-4' : ''}`}>
              <h3 className="text-md font-semibold mb-2">
                基本信息
                {changes.meta && <span className="text-xs text-yellow-600 ml-2">(已修改)</span>}
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm text-gray-500 mb-1">主题</label>
                  <input
                    type="text"
                    value={lesson.meta.topic}
                    onChange={(e) => updateMeta('topic', e.target.value)}
                    className="w-full rounded border border-gray-300 px-3 py-1.5 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">学科</label>
                  <input
                    type="text"
                    value={lesson.meta.subject}
                    onChange={(e) => updateMeta('subject', e.target.value)}
                    className="w-full rounded border border-gray-300 px-3 py-1.5 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">年级</label>
                  <input
                    type="text"
                    value={lesson.meta.grade}
                    onChange={(e) => updateMeta('grade', e.target.value)}
                    className="w-full rounded border border-gray-300 px-3 py-1.5 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">时长(分钟)</label>
                  <input
                    type="number"
                    value={lesson.meta.duration}
                    onChange={(e) => updateMeta('duration', parseInt(e.target.value) || 0)}
                    className="w-full rounded border border-gray-300 px-3 py-1.5 text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Outline sections */}
            <div className="space-y-3">
              <h3 className="text-md font-semibold">课程大纲</h3>
              {lesson.outline.map((section) => (
                <div
                  key={section.section_id}
                  className={`border rounded p-3 ${
                    changes.sections.has(section.section_id)
                      ? 'border-yellow-400 bg-yellow-50'
                      : 'border-gray-200'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm font-medium text-gray-500">
                      {section.section_id}.
                    </span>
                    <input
                      type="text"
                      value={section.title}
                      onChange={(e) => updateSection(section.section_id, 'title', e.target.value)}
                      className="flex-1 rounded border border-gray-300 px-2 py-1 text-sm font-medium"
                    />
                    {changes.sections.has(section.section_id) && (
                      <span className="text-xs text-yellow-600">(已修改)</span>
                    )}
                  </div>
                  <textarea
                    value={section.content}
                    onChange={(e) => updateSection(section.section_id, 'content', e.target.value)}
                    className="w-full rounded border border-gray-300 px-2 py-1 text-sm min-h-20"
                    placeholder="章节内容"
                  />
                  <div className="mt-2 grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">教学要点</label>
                      <textarea
                        value={section.teaching_points.join('\n')}
                        onChange={(e) => updateTeachingPoints(
                          section.section_id,
                          e.target.value.split('\n').filter(Boolean)
                        )}
                        className="w-full rounded border border-gray-300 px-2 py-1 text-xs"
                        placeholder="每行一个要点"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">例子</label>
                      <textarea
                        value={section.examples.join('\n')}
                        onChange={(e) => updateExamples(
                          section.section_id,
                          e.target.value.split('\n').filter(Boolean)
                        )}
                        className="w-full rounded border border-gray-300 px-2 py-1 text-xs"
                        placeholder="每行一个例子"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Summary section */}
            <div className={`border-t pt-4 ${changes.summary ? 'bg-yellow-50 -mx-4 px-4' : ''}`}>
              <h3 className="text-md font-semibold mb-2">
                总结
                {changes.summary && <span className="text-xs text-yellow-600 ml-2">(已修改)</span>}
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm text-gray-500 mb-1">核心要点</label>
                  <textarea
                    value={lesson.summary.key_points.join('\n')}
                    onChange={(e) => updateSummary('key_points', e.target.value.split('\n').filter(Boolean))}
                    className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
                    placeholder="每行一个要点"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">作业</label>
                  <input
                    type="text"
                    value={lesson.summary.homework}
                    onChange={(e) => updateSummary('homework', e.target.value)}
                    className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-500 mb-1">下节预告</label>
                  <input
                    type="text"
                    value={lesson.summary.next_preview}
                    onChange={(e) => updateSummary('next_preview', e.target.value)}
                    className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
                  />
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* JSON mode */
          <textarea
            value={jsonText}
            onChange={(e) => handleJsonEdit(e.target.value)}
            className="w-full min-h-96 rounded border border-gray-300 px-3 py-2 font-mono text-sm"
            spellCheck={false}
          />
        )}
      </div>

      {/* Action buttons */}
      {hasChanges && (
        <div className="flex gap-3">
          <button
            onClick={handleSave}
            disabled={isSaving || !hasChanges}
            className={`px-4 py-2 rounded font-medium ${
              isSaving || !hasChanges
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {isSaving ? '保存中...' : '保存'}
          </button>
          {changes.sections.size > 0 && (
            <button
              onClick={handleRegenerate}
              disabled={isRegenerating}
              className={`px-4 py-2 rounded font-medium ${
                isRegenerating
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-green-600 text-white hover:bg-green-700'
              }`}
            >
              {isRegenerating ? '重新生成中...' : `重新生成 (${changes.sections.size} 章节)`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}