import StatePanel from "./StatePanel";
import UsagePanel from "./UsagePanel";
import type { Conversation, Usage } from "../types";

interface SidebarProps {
  conversations: Conversation[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  onCreate: () => void;
  isLoading: boolean;
  error: string | null;
  userEmail: string;
  onLogout: () => void;
  usage: Usage | null;
  usageLoading: boolean;
  usageError: string | null;
}

export default function Sidebar({
  conversations,
  selectedId,
  onSelect,
  onCreate,
  isLoading,
  error,
  userEmail,
  onLogout,
  usage,
  usageLoading,
  usageError,
}: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-brand">AI Chat Platform</span>
      </div>

      <button type="button" className="sidebar-new-btn" onClick={onCreate}>
        + New conversation
      </button>

      <nav className="conversation-list" aria-label="Conversations">
        {isLoading && <StatePanel tone="muted" title="Loading conversations…" />}
        {error && <StatePanel tone="error" title={error} />}
        {!isLoading && !error && conversations.length === 0 && (
          <StatePanel tone="empty" title="No conversations yet">
            Start one above to begin chatting.
          </StatePanel>
        )}
        {conversations.map((conversation) => (
          <button
            type="button"
            key={conversation.id}
            className={`conversation-item${conversation.id === selectedId ? " active" : ""}`}
            onClick={() => onSelect(conversation.id)}
            aria-current={conversation.id === selectedId}
          >
            {conversation.title}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <UsagePanel usage={usage} isLoading={usageLoading} error={usageError} />
        <div className="sidebar-user">
          <span className="sidebar-user-email" title={userEmail}>
            {userEmail}
          </span>
          <button type="button" className="sidebar-logout-btn" onClick={onLogout}>
            Log out
          </button>
        </div>
      </div>
    </aside>
  );
}
