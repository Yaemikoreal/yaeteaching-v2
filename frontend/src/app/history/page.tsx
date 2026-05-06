'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { HistoryList } from '@/components';
import { getHistoryList, deleteHistory, toggleStar } from '@/lib/api';
import type {
  HistoryItem,
  HistoryListParams,
  HistoryListResponse,
} from '@/types';

export default function HistoryPage() {
  const [historyData, setHistoryData] = useState<HistoryListResponse | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useState<HistoryListParams>({
    page: 1,
    limit: 20,
  });

  const loadHistory = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getHistoryList(searchParams);
      setHistoryData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载历史记录失败');
    } finally {
      setIsLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const handleSearch = (search: string) => {
    setSearchParams((prev) => ({ ...prev, search, page: 1 }));
  };

  const handleFilterChange = (filters: Partial<HistoryListParams>) => {
    setSearchParams((prev) => ({ ...prev, ...filters, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setSearchParams((prev) => ({ ...prev, page }));
  };

  const handleDelete = async (historyId: string) => {
    try {
      await deleteHistory(historyId);
      loadHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败');
    }
  };

  const handleToggleStar = async (historyId: string) => {
    try {
      const updatedItem = await toggleStar(historyId);
      setHistoryData((prev) =>
        prev
          ? {
              ...prev,
              items: prev.items.map((item) =>
                item.id === historyId ? updatedItem : item
              ),
            }
          : null
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : '收藏失败');
    }
  };

  return (
    <div className="min-h-full flex flex-col bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">历史记录</h1>
            <p className="text-sm text-gray-500 mt-1">
              查看和管理已生成的教案历史
            </p>
          </div>
          <Link
            href="/"
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm font-medium"
          >
            新建教案
          </Link>
        </div>
      </header>

      <main className="flex-1 px-4 py-8">
        <div className="max-w-7xl mx-auto">
          {error && (
            <div className="rounded-lg bg-red-50 p-4 text-sm text-red-600 mb-4">
              {error}
            </div>
          )}

          <HistoryList
            items={historyData?.items || []}
            isLoading={isLoading}
            total={historyData?.total || 0}
            page={searchParams.page || 1}
            limit={searchParams.limit || 20}
            hasMore={historyData?.hasMore || false}
            search={searchParams.search}
            starred={searchParams.starred}
            onSearch={handleSearch}
            onFilterChange={handleFilterChange}
            onPageChange={handlePageChange}
            onDelete={handleDelete}
            onToggleStar={handleToggleStar}
          />
        </div>
      </main>

      <footer className="bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-7xl mx-auto text-center text-sm text-gray-500">
          AI教案生成工作站 — Multica Platform
        </div>
      </footer>
    </div>
  );
}