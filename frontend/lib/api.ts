const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

interface ApiOptions extends RequestInit {
  token?: string | null;
}

let redirectingToLogin = false;

function handleUnauthorized() {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.removeItem("access_token");

  if (
    window.location.pathname === "/login" ||
    window.location.pathname === "/register"
  ) {
    return;
  }

  if (!redirectingToLogin) {
    redirectingToLogin = true;

    const currentPath =
      window.location.pathname +
      window.location.search;

    const next = encodeURIComponent(currentPath);

    window.location.href = `/login?next=${next}`;
  }
}

async function extractErrorMessage(
  response: Response,
): Promise<string> {
  try {
    const body = await response.json();

    if (typeof body?.detail === "string") {
      return body.detail;
    }

    if (body?.detail) {
      return JSON.stringify(body.detail);
    }

    if (typeof body?.message === "string") {
      return body.message;
    }
  } catch {
    // Response wasn't JSON.
  }

  return `Request failed with status ${response.status}`;
}

export async function apiFetch<T>(
  path: string,
  options: ApiOptions = {},
): Promise<T> {
  const {
    token,
    headers,
    ...requestOptions
  } = options;

  const requestHeaders = new Headers(headers);

  if (
    requestOptions.body &&
    !(requestOptions.body instanceof FormData)
  ) {
    requestHeaders.set(
      "Content-Type",
      "application/json",
    );
  }

  const authToken =
    token ??
    (typeof window !== "undefined"
      ? localStorage.getItem("access_token")
      : null);

  if (authToken) {
    requestHeaders.set(
      "Authorization",
      `Bearer ${authToken}`,
    );
  }

  let response: Response;

  try {
    response = await fetch(
      `${API_URL}${path}`,
      {
        ...requestOptions,
        headers: requestHeaders,
        cache: "no-store",
      },
    );
  } catch {
    throw new Error(
      "Unable to connect to the ContextAI backend. Make sure the FastAPI server is running.",
    );
  }

  if (response.status === 401) {
    handleUnauthorized();

    throw new Error(
      "Your session has expired. Please log in again.",
    );
  }

  if (!response.ok) {
    throw new Error(
      await extractErrorMessage(response),
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function apiUpload<T>(
  path: string,
  formData: FormData,
): Promise<T> {
  return apiFetch<T>(
    path,
    {
      method: "POST",
      body: formData,
    },
  );
}

export { API_URL };