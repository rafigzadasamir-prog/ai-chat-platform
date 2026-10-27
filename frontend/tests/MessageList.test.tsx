import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import MessageList from "../src/components/MessageList";
import type { Message } from "../src/types";

const sampleMessages: Message[] = [
  { id: 1, role: "user", content: "What is the refund policy?", created_at: "2026-01-01T00:00:00Z" },
  {
    id: 2,
    role: "assistant",
    content: "Here you go:\n\n- Refunds in 14 days\n- Email billing@example.com",
    created_at: "2026-01-01T00:00:05Z",
  },
];

describe("MessageList", () => {
  it("shows a loading state", () => {
    render(<MessageList messages={[]} streaming={null} isLoading={true} error={null} />);
    expect(screen.getByText("Loading conversation…")).toBeInTheDocument();
  });

  it("shows an error state", () => {
    render(
      <MessageList messages={[]} streaming={null} isLoading={false} error="Network unreachable" />,
    );
    expect(screen.getByText("Network unreachable")).toBeInTheDocument();
  });

  it("shows an empty state when there are no messages and nothing is streaming", () => {
    render(<MessageList messages={[]} streaming={null} isLoading={false} error={null} />);
    expect(screen.getByText("No messages yet")).toBeInTheDocument();
  });

  it("renders user and assistant messages, with the assistant's markdown converted to HTML", () => {
    render(<MessageList messages={sampleMessages} streaming={null} isLoading={false} error={null} />);

    expect(screen.getByText("What is the refund policy?")).toBeInTheDocument();
    // marked's GFM autolinking turns the email into a real mailto link.
    expect(screen.getByText("billing@example.com")).toBeInTheDocument();
    // "- Refunds in 14 days" should become a real <li>, not literal markdown.
    const listItem = screen.getByText("Refunds in 14 days");
    expect(listItem.tagName.toLowerCase()).toBe("li");
  });

  it("renders a trailing StreamingMessage while a response is streaming", () => {
    render(
      <MessageList
        messages={sampleMessages}
        streaming={{ content: "Partial answer…", isStreaming: true }}
        isLoading={false}
        error={null}
      />,
    );
    expect(screen.getByTestId("streaming-message")).toBeInTheDocument();
    expect(screen.getByText("Partial answer…")).toBeInTheDocument();
  });
});
