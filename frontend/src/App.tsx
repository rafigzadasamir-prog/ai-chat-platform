import { useState } from "react";
import ChatPage from "./pages/ChatPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import StatePanel from "./components/StatePanel";
import { AuthProvider, useAuth } from "./context/AuthContext";

function AppShell() {
  const { token, user, isBootstrapping } = useAuth();
  const [authView, setAuthView] = useState<"login" | "register">("login");

  if (token && isBootstrapping) {
    return (
      <div className="bootstrap-screen">
        <StatePanel tone="muted" title="Loading your account…" />
      </div>
    );
  }

  if (!token || !user) {
    return authView === "login" ? (
      <LoginPage onSwitchToRegister={() => setAuthView("register")} />
    ) : (
      <RegisterPage onSwitchToLogin={() => setAuthView("login")} />
    );
  }

  return <ChatPage />;
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}
