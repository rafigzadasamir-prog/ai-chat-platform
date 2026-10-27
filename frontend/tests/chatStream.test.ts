import { afterEach, describe, expect, it, vi } from "vitest";
import { sendMessageStream } from "../src/api/chatStream";

function streamResponseFrom(rawChunks: string[], ok = true): Response {
  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of rawChunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
  return { ok, body, statusText: "OK" } as unknown as Response;
}

describe("sendMessageStream", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("reassembles chunks split across arbitrary network read boundaries", async () => {
    // Deliberately split the SSE payload mid-line and mid-JSON-object so the
    // buffering logic in streamSSE() must reassemble it correctly.
    const rawChunks = [
      'data: {"chunk":"Hel"}\n\ndata: {"chunk":"lo ',
      '"}\n\ndata: {"chunk":"world"}\n\nevent: done\n',
      'data: {"message_id":42}\n\n',
    ];
    vi.spyOn(globalThis, "fetch").mockResolvedValue(streamResponseFrom(rawChunks));

    const chunks: string[] = [];
    let doneMessageId: number | null = null;
    const onError = vi.fn();

    await sendMessageStream("fake-token", 1, "hi", {
      onChunk: (chunk) => chunks.push(chunk),
      onDone: (messageId) => {
        doneMessageId = messageId;
      },
      onError,
    });

    expect(chunks).toEqual(["Hel", "lo ", "world"]);
    expect(doneMessageId).toBe(42);
    expect(onError).not.toHaveBeenCalled();
  });

  it("sends the Authorization header and JSON body to the right URL", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(streamResponseFrom(['event: done\ndata: {"message_id":1}\n\n']));

    await sendMessageStream("my-token", 5, "hello there", {
      onChunk: vi.fn(),
      onDone: vi.fn(),
      onError: vi.fn(),
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toContain("/conversations/5/messages");
    expect(init?.headers).toMatchObject({ Authorization: "Bearer my-token" });
    expect(JSON.parse(init?.body as string)).toEqual({ content: "hello there" });
  });

  it("surfaces a non-OK response as onError instead of throwing", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 429,
      statusText: "Too Many Requests",
      json: async () => ({ detail: "Rate limit exceeded. Please slow down." }),
    } as unknown as Response);

    const onError = vi.fn();
    await sendMessageStream("token", 1, "hi", {
      onChunk: vi.fn(),
      onDone: vi.fn(),
      onError,
    });

    expect(onError).toHaveBeenCalledWith("Rate limit exceeded. Please slow down.");
  });

  it("surfaces a network failure as onError", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("network down"));

    const onError = vi.fn();
    await sendMessageStream("token", 1, "hi", { onChunk: vi.fn(), onDone: vi.fn(), onError });

    expect(onError).toHaveBeenCalledWith(expect.stringContaining("Network error"));
  });
});
