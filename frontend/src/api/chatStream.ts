import { API_BASE_URL } from "./client";
import { streamSSE } from "../lib/sse";

export interface ChatStreamCallbacks {
  onChunk: (chunk: string) => void;
  onDone: (messageId: number) => void;
  onError: (message: string) => void;
}

interface ChunkPayload {
  chunk: string;
}

interface DonePayload {
  message_id: number;
}

interface ErrorPayload {
  detail: string;
}

/**
 * POST a user message and consume the backend's Server-Sent-Events
 * response, invoking callbacks as chunks arrive. The backend's streaming
 * endpoint is POST-only, so this uses fetch + a manual reader rather than
 * the browser's native (GET-only) EventSource.
 */
export async function sendMessageStream(
  token: string,
  conversationId: number,
  content: string,
  callbacks: ChatStreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ content }),
      signal,
    });
  } catch {
    callbacks.onError("Network error: could not reach the server.");
    return;
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // No JSON body (e.g. a plain-text 429) -- fall back to statusText.
    }
    callbacks.onError(detail || "Request failed.");
    return;
  }

  try {
    for await (const event of streamSSE(response)) {
      if (!event.data) continue;
      if (event.event === "done") {
        const payload = JSON.parse(event.data) as DonePayload;
        callbacks.onDone(payload.message_id);
      } else if (event.event === "error") {
        const payload = JSON.parse(event.data) as ErrorPayload;
        callbacks.onError(payload.detail);
      } else {
        const payload = JSON.parse(event.data) as ChunkPayload;
        callbacks.onChunk(payload.chunk);
      }
    }
  } catch {
    callbacks.onError("The connection to the AI backend was interrupted.");
  }
}
