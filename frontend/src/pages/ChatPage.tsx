import { useCallback, useEffect, useState } from "react";
import DocumentUpload from "../components/DocumentUpload";
import MessageInput from "../components/MessageInput";
import MessageList from "../components/MessageList";
import Sidebar from "../components/Sidebar";
import StatePanel from "../components/StatePanel";
import { sendMessageStream } from "../api/chatStream";
import { ApiError, api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import type { Conversation, DocumentInfo, Message, Usage } from "../types";

function errorMessageOf(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback;
}

export default function ChatPage() {
  const { token, user, logout } = useAuth();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationsLoading, setConversationsLoading] = useState(true);
  const [conversationsError, setConversationsError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [messagesError, setMessagesError] = useState<string | null>(null);

  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [documentError, setDocumentError] = useState<string | null>(null);

  const [usage, setUsage] = useState<Usage | null>(null);
  const [usageLoading, setUsageLoading] = useState(true);
  const [usageError, setUsageError] = useState<string | null>(null);

  const [streaming, setStreaming] = useState<{ content: string; isStreaming: boolean } | null>(
    null,
  );
  const [sendError, setSendError] = useState<string | null>(null);

  const loadUsage = useCallback(async () => {
    if (!token) return;
    setUsageLoading(true);
    setUsageError(null);
    try {
      setUsage(await api.getUsage(token));
    } catch (err) {
      setUsageError(errorMessageOf(err, "Could not load usage."));
    } finally {
      setUsageLoading(false);
    }
  }, [token]);

  const loadConversations = useCallback(async () => {
    if (!token) return;
    setConversationsLoading(true);
    setConversationsError(null);
    try {
      const data = await api.listConversations(token);
      setConversations(data);
      setSelectedId((current) => current ?? data[0]?.id ?? null);
    } catch (err) {
      setConversationsError(errorMessageOf(err, "Could not load conversations."));
    } finally {
      setConversationsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void loadConversations();
    void loadUsage();
  }, [loadConversations, loadUsage]);

  useEffect(() => {
    if (!token || selectedId == null) {
      setMessages([]);
      setDocuments([]);
      return;
    }
    let cancelled = false;
    setMessagesLoading(true);
    setMessagesError(null);
    setDocumentError(null);

    Promise.all([api.listMessages(token, selectedId), api.listDocuments(token, selectedId)])
      .then(([loadedMessages, loadedDocuments]) => {
        if (cancelled) return;
        setMessages(loadedMessages);
        setDocuments(loadedDocuments);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setMessagesError(errorMessageOf(err, "Could not load this conversation."));
      })
      .finally(() => {
        if (!cancelled) setMessagesLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token, selectedId]);

  async function handleCreateConversation() {
    if (!token) return;
    try {
      const conversation = await api.createConversation(token);
      setConversations((prev) => [conversation, ...prev]);
      setSelectedId(conversation.id);
    } catch (err) {
      setConversationsError(errorMessageOf(err, "Could not create a conversation."));
    }
  }

  async function handleUpload(file: File) {
    if (!token || selectedId == null) return;
    setIsUploading(true);
    setDocumentError(null);
    try {
      const info = await api.uploadDocument(token, selectedId, file);
      setDocuments((prev) => [...prev.filter((doc) => doc.document_name !== info.document_name), info]);
    } catch (err) {
      setDocumentError(errorMessageOf(err, "Could not upload the document."));
    } finally {
      setIsUploading(false);
    }
  }

  function handleSend(content: string) {
    if (!token || selectedId == null || streaming) return;
    setSendError(null);

    const optimisticUserMessage: Message = {
      id: -Date.now(),
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUserMessage]);
    setStreaming({ content: "", isStreaming: true });

    void sendMessageStream(token, selectedId, content, {
      onChunk: (chunk) => {
        setStreaming((prev) => (prev ? { ...prev, content: prev.content + chunk } : prev));
      },
      onDone: (messageId) => {
        setStreaming((prev) => {
          if (prev) {
            setMessages((prevMessages) => [
              ...prevMessages,
              {
                id: messageId,
                role: "assistant",
                content: prev.content,
                created_at: new Date().toISOString(),
              },
            ]);
          }
          return null;
        });
        void loadUsage();
      },
      onError: (message) => {
        setSendError(message);
        setStreaming(null);
      },
    });
  }

  if (!user) return null;

  const selectedConversation = conversations.find((c) => c.id === selectedId) ?? null;

  return (
    <div className="app-shell">
      <Sidebar
        conversations={conversations}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onCreate={handleCreateConversation}
        isLoading={conversationsLoading}
        error={conversationsError}
        userEmail={user.email}
        onLogout={logout}
        usage={usage}
        usageLoading={usageLoading}
        usageError={usageError}
      />
      <main className="chat-panel">
        {selectedConversation ? (
          <>
            <header className="chat-panel-header">
              <h1>{selectedConversation.title}</h1>
              <DocumentUpload
                documents={documents}
                onUpload={handleUpload}
                isUploading={isUploading}
                errorMessage={documentError}
              />
            </header>
            <MessageList
              messages={messages}
              streaming={streaming}
              isLoading={messagesLoading}
              error={messagesError}
            />
            {sendError && (
              <p className="send-error" role="alert">
                {sendError}
              </p>
            )}
            <MessageInput onSend={handleSend} disabled={streaming !== null} />
          </>
        ) : (
          <div className="chat-panel-empty">
            <StatePanel tone="empty" title={`Welcome, ${user.email}`}>
              Create a new conversation from the sidebar to get started.
            </StatePanel>
          </div>
        )}
      </main>
    </div>
  );
}
