'use client';

import { useState } from 'react';
import type { HistoryItem, HistoryListParams } from '@/types';

interface HistoryListProps {
  items: HistoryItem[];
  isLoading: boolean;
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
  search?: string;
  starred?: boolean;
  onSearch: (search: string) => void;
  onFilterChange: (filters: Partial<HistoryListParams>) => void;
  onPageChange: (page: number) => void;
  onDelete: (historyId: string) => void;
  onToggleStar: (historyId: string) => void;
}

export function HistoryList({
  items,
  isLoading,
  total,
  page,
  limit,
  hasMore,
  search,
  starred,
  onSearch,
  onFilterChange,
  onPageChange,
  onDelete,
  onToggleStar,
}: HistoryListProps) {
  const [searchInput, setSearchInput] = useState(search || '');
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(searchInput);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusBadge = (status: HistoryItem['status']) => {
    const statusConfig = {
      pending: { text: '等待中', className: 'bg-gray-100 text-gray-600' },
      in_progress: { text: '进行中', className: 'bg-blue-100 text-blue-600' },
      completed: { text: '已完成', className: 'bg-green-100 text-green-600' },
      failed: { text: '失败', className: 'bg-red-100 text-red-600' },
    };
    const config = statusConfig[status];
    return (
      <span
        className={`px-2 py-1 rounded text-xs font-medium ${config.className}`}
      >
        {config.text}
      </span>
    );
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-4">
      {/* Search and Filter */}
      <div className="rounded-lg bg-white p-4 shadow-sm">
        <form onSubmit={handleSearchSubmit} className="flex gap-2 mb-4">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="搜索主题或学科..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            搜索
          </button>
        </form>

        <div className="flex gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={starred || false}
              onChange={(e) => onFilterChange({ starred: e.target.checked })}
              className="w-4 h-4 text-blue-500 rounded focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">只显示收藏</span>
          </label>
        </div>
      </div>

      {/* Results count */}
      <div className="text-sm text-gray-600">
        共 {total} 条记录，当前第 {page} 页
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="rounded-lg bg-white p-8 text-center">
          <div className="inline-block w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="mt-2 text-gray-600">加载中...</p>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && items.length === 0 && (
        <div className="rounded-lg bg-white p-8 text-center">
          <p className="text-gray-600">
            {search || starred ? '未找到匹配的历史记录' : '暂无历史记录'}
          </p>
        </div>
      )}

      {/* History items */}
      {!isLoading && items.length > 0 && (
        <div className="rounded-lg bg-white shadow-sm divide-y divide-gray-200">
          {items.map((item) => (
            <div
              key={item.id}
              className="p-4 flex items-start justify-between hover:bg-gray-50 transition-colors"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-base font-medium text-gray-900">
                    {item.topic}
                  </h3>
                  {getStatusBadge(item.status)}
                  {item.starred && (
                    <span className="text-yellow-500">★</span>
                  )}
                </div>

                <div className="flex gap-4 text-sm text-gray-500">
                  <span>{item.subject}</span>
                  <span>{item.grade}</span>
                  <span>{item.duration}分钟</span>
                  <span>{formatDate(item.createdAt)}</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => onToggleStar(item.id)}
                  className={`px-3 py-1.5 rounded text-sm ${
                    item.starred
                      ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  } transition-colors`}
                >
                  {item.starred ? '取消收藏' : '收藏'}
                </button>

                {deleteConfirm === item.id ? (
                  <div className="flex gap-1">
                    <button
                      onClick={() => {
                        onDelete(item.id);
                        setDeleteConfirm(null);
                      }}
                      className="px-3 py-1.5 bg-red-500 text-white rounded text-sm hover:bg-red-600 transition-colors"
                    >
                      确认
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(null)}
                      className="px-3 py-1.5 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300 transition-colors"
                    >
                      取消
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setDeleteConfirm(item.id)}
                    className="px-3 py-1.5 bg-red-100 text-red-600 rounded text-sm hover:bg-red-200 transition-colors"
                  >
                    删除
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {!isLoading && totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className={`px-4 py-2 rounded ${
              page <= 1
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            } transition-colors`}
          >
            上一页
          </button>

          <span className="px-4 py-2 text-gray-600">
            {page} / {totalPages}
          </span>

          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className={`px-4 py-2 rounded ${
              page >= totalPages
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            } transition-colors`}
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
}