'use client';

interface SectionRegenerationStatus {
  sectionId: number;
  title: string;
  status: 'pending' | 'regenerating' | 'completed' | 'failed';
  progress: number; // 0-100
  error?: string;
}

interface RegenerationProgressProps {
  sections: SectionRegenerationStatus[];
  onComplete?: () => void;
}

export function RegenerationProgress({
  sections,
  onComplete,
}: RegenerationProgressProps) {
  if (sections.length === 0) return null;

  const allCompleted = sections.every(
    (s) => s.status === 'completed' || s.status === 'failed'
  );

  // Trigger onComplete when all sections are done
  if (allCompleted && onComplete) {
    // Use setTimeout to avoid calling during render
    setTimeout(onComplete, 0);
  }

  return (
    <div className="w-full space-y-3 rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-md font-semibold text-gray-800">
          重新生成进度
        </h3>
        {allCompleted && (
          <span className="text-sm text-green-600 font-medium">完成</span>
        )}
      </div>

      {/* Overall progress */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-2 rounded bg-gray-200 overflow-hidden">
          <div
            className="h-full bg-blue-600 transition-all duration-300"
            style={{
              width: `${Math.round(
                sections.reduce((sum, s) => sum + s.progress, 0) / sections.length
              )}%`,
            }}
          />
        </div>
        <span className="text-sm text-gray-500">
          {Math.round(
            sections.reduce((sum, s) => sum + s.progress, 0) / sections.length
          )}%
        </span>
      </div>

      {/* Section list */}
      <div className="space-y-2">
        {sections.map((section) => (
          <div
            key={section.sectionId}
            className="flex items-center gap-2 text-sm"
          >
            {/* Status icon */}
            <div className="w-4 h-4 flex items-center justify-center">
              {section.status === 'pending' && (
                <div className="w-3 h-3 rounded-full border-2 border-gray-300" />
              )}
              {section.status === 'regenerating' && (
                <div className="w-3 h-3 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
              )}
              {section.status === 'completed' && (
                <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
              {section.status === 'failed' && (
                <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              )}
            </div>

            {/* Section info */}
            <span className="text-gray-600">
              {section.sectionId}. {section.title}
            </span>

            {/* Progress */}
            {section.status === 'regenerating' && (
              <span className="text-blue-600">{section.progress}%</span>
            )}
            {section.status === 'failed' && section.error && (
              <span className="text-red-600 text-xs">{section.error}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}