'use client';

import { useState } from 'react';
import { useAuthStore } from '@/store';
import { z } from 'zod';

const registerSchema = z.object({
  email: z.string().email('请输入有效的邮箱地址'),
  password: z.string().min(6, '密码至少需要6个字符'),
  name: z.string().min(2, '姓名至少需要2个字符').optional(),
});

interface RegisterFormProps {
  onSuccess?: () => void;
  onSwitchToLogin?: () => void;
}

export function RegisterForm({ onSuccess, onSwitchToLogin }: RegisterFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const { registerAction, isLoading, error, clearError } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setValidationErrors({});

    // Validate form
    const result = registerSchema.safeParse({ email, password, name: name || undefined });
    if (!result.success) {
      const errors: Record<string, string> = {};
      result.error.issues.forEach((err) => {
        if (err.path[0]) {
          errors[err.path[0] as string] = err.message;
        }
      });
      setValidationErrors(errors);
      return;
    }

    try {
      await registerAction({ email, password, name: name || undefined });
      onSuccess?.();
    } catch {
      // Error is handled in the store
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-md space-y-6">
      <div className="space-y-2">
        <label
          htmlFor="name"
          className="block text-sm font-medium text-gray-700"
        >
          姓名（可选）
        </label>
        <input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="请输入姓名"
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {validationErrors.name && (
          <p className="text-sm text-red-600">{validationErrors.name}</p>
        )}
      </div>

      <div className="space-y-2">
        <label
          htmlFor="register-email"
          className="block text-sm font-medium text-gray-700"
        >
          邮箱
        </label>
        <input
          id="register-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="请输入邮箱"
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {validationErrors.email && (
          <p className="text-sm text-red-600">{validationErrors.email}</p>
        )}
      </div>

      <div className="space-y-2">
        <label
          htmlFor="register-password"
          className="block text-sm font-medium text-gray-700"
        >
          密码
        </label>
        <input
          id="register-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="请输入密码（至少6个字符）"
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {validationErrors.password && (
          <p className="text-sm text-red-600">{validationErrors.password}</p>
        )}
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="w-full rounded-lg bg-blue-600 px-4 py-3 text-white font-medium transition-colors hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {isLoading ? '注册中...' : '注册'}
      </button>

      {onSwitchToLogin && (
        <div className="text-center">
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="text-sm text-blue-600 hover:underline"
          >
            已有账号？点击登录
          </button>
        </div>
      )}
    </form>
  );
}