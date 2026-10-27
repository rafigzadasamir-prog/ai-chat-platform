import { useState } from "react";
import type { FormEvent } from "react";
import AuthLayout from "./AuthLayout";
import { useAuth } from "../context/AuthContext";
import { MIN_PASSWORD_LENGTH, isValidEmail, isValidPassword } from "../lib/validation";

interface RegisterPageProps {
  onSwitchToLogin: () => void;
}

export default function RegisterPage({ onSwitchToLogin }: RegisterPageProps) {
  const { register, isSubmitting, authError } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);

    if (!isValidEmail(email)) {
      setFormError("Enter a valid email address.");
      return;
    }
    if (!isValidPassword(password)) {
      setFormError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters.`);
      return;
    }
    if (password !== confirmPassword) {
      setFormError("Passwords do not match.");
      return;
    }

    try {
      await register(email, password);
    } catch {
      setFormError(authError ?? "Could not create your account. Please try again.");
    }
  }

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Start chatting with your AI assistant in seconds."
      footer={
        <>
          Already have an account?{" "}
          <button type="button" className="link-button" onClick={onSwitchToLogin}>
            Log in
          </button>
        </>
      }
    >
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <label htmlFor="register-email">Email</label>
        <input
          id="register-email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
        />

        <label htmlFor="register-password">Password</label>
        <input
          id="register-password"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder={`At least ${MIN_PASSWORD_LENGTH} characters`}
        />

        <label htmlFor="register-confirm-password">Confirm password</label>
        <input
          id="register-confirm-password"
          type="password"
          autoComplete="new-password"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          placeholder="••••••••"
        />

        {formError && (
          <p className="auth-error" role="alert">
            {formError}
          </p>
        )}

        <button type="submit" className="auth-submit-btn" disabled={isSubmitting}>
          {isSubmitting ? "Creating account…" : "Create account"}
        </button>
      </form>
    </AuthLayout>
  );
}
