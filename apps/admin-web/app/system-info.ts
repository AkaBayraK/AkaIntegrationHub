export interface SystemInfo {
  product: string;
  version: string;
  environment: string;
}

const API_URL = process.env.AIH_API_URL ?? 'http://localhost:28080';

export async function fetchSystemInfo(): Promise<SystemInfo | null> {
  try {
    const response = await fetch(`${API_URL}/v1/system/info`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(2000),
    });
    return response.ok ? ((await response.json()) as SystemInfo) : null;
  } catch {
    return null;
  }
}
