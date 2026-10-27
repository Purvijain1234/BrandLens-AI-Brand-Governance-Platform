const API_BASE = 'http://localhost:8000';

export async function apiRequest(endpoint: string, options: RequestInit = {}, role: string = 'Creator') {
  const headers = new Headers(options.headers || {});
  headers.set('X-User-Role', role.toLowerCase());
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch (e) {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}
