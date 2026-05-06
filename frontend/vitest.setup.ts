import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

// Stub environment variables for tests
vi.stubEnv('NEXT_PUBLIC_WS_URL', 'ws://localhost:8000');