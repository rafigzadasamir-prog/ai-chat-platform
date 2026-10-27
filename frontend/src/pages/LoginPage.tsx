import { useState } from "react";
import type { FormEvent } from "react";
import AuthLayout from "./AuthLayout";
import { useAuth } from "../context/AuthContext";
import { isValidEmail } from "../lib/validation";

interface LoginPageProps {
  onSwitchToRegister: () => void;
}

export default function LoginPage({ onSwitchToRegister }: LoginPageProps) {
  const { login, isSubmitting } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);

    if (!isValidEmail(email)) {
      setFormError("Enter a valid email address.");
      return;
    }
    if (password.length === 0) {
      setFormError("Enter your password.");
      return;
    }

    try {
      await login(email, password);
    } catch {
      setFormError("Invalid email or password.");
    }
  }

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Log in to continue your conversations."
      footer={
        <>
          Don&apos;t have an account?{" "}
          <button type="button" className="link-button" onClick={onSwitchToRegister}>
            Create one
          </button>
        </>
      }
    >
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <label htmlFor="login-email">Email</label>
        <input
          id="login-email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
        />

        <label htmlFor="login-password">Password</label>
        <input
          id="login-password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="••••••••"
        />

        {formError && (
          <p className="auth-error" role="alert">
            {formError}
          </p>
        )}

        <button type="submit" className="auth-submit-btn" disabled={isSubmitting}>
          {isSubmitting ? "Logging in…" : "Log in"}
        </button>
      </form>
    </AuthLayout>
  );
}
