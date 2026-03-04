// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const API_BASE_URL: string =
  ((import.meta as any).env?.VITE_API_URL as string | undefined) ??
  'http://localhost:8000';
