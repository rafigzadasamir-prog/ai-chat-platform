import type { AuthToken, Conversation, DocumentInfo, Message, Usage, User } from "../types";

export const API_BASE_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    if (body.detail) return body.detail;
    return JSON.stringify(body);
  } catch {
    return response.statusText || `Request failed with status ${response.status}`;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  if (options.body && !isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    throw new ApiError(response.status, await readErrorDetail(response));
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  register(email: string, password: string): Promise<User> {
    return request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  login(email: string, password: string): Promise<AuthToken> {
    return request<AuthToken>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  me(token: string): Promise<User> {
    return request<User>("/auth/me", {}, token);
  },

  createConversation(token: string, title?: string): Promise<Conversation> {
    return request<Conversation>(
      "/conversations",
      { method: "POST", body: JSON.stringify({ title }) },
      token,
    );
  },

  listConversations(token: string): Promise<Conversation[]> {
    return request<Conversation[]>("/conversations", {}, token);
  },

  listMessages(token: string, conversationId: number): Promise<Message[]> {
    return request<Message[]>(`/conversations/${conversationId}/messages`, {}, token);
  },

  uploadDocument(token: string, conversationId: number, file: File): Promise<DocumentInfo> {
    const formData = new FormData();
    formData.append("file", file);
    return request<DocumentInfo>(
      `/conversations/${conversationId}/documents`,
      { method: "POST", body: formData },
      token,
    );
  },

  listDocuments(token: string, conversationId: number): Promise<DocumentInfo[]> {
    return request<DocumentInfo[]>(`/conversations/${conversationId}/documents`, {}, token);
  },

  getUsage(token: string): Promise<Usage> {
    return request<Usage>("/usage", {}, token);
  },
};
