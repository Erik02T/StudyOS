export async function apiRequest({
  baseUrl,
  token,
  organizationId,
  path,
  method = "GET",
  body,
  headers: customHeaders,
}) {
  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(organizationId ? { "X-Organization-Id": String(organizationId) } : {}),
      ...(customHeaders || {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const fallback = `HTTP ${response.status}`;
    let message = fallback;
    try {
      const payload = await response.json();
      message = payload.detail || JSON.stringify(payload);
    } catch (_error) {
      message = fallback;
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }
  return response.json();
}
