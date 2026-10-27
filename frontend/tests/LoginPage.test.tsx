import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import LoginPage from "../src/pages/LoginPage";
import { AuthProvider } from "../src/context/AuthContext";

function renderLoginPage() {
  const onSwitchToRegister = vi.fn();
  render(
    <AuthProvider>
      <LoginPage onSwitchToRegister={onSwitchToRegister} />
    </AuthProvider>,
  );
  return { onSwitchToRegister };
}

describe("LoginPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("rejects an invalid email address without calling the API", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    renderLoginPage();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText("Email"), "not-an-email");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Enter a valid email address.");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("requires a password to be entered", async () => {
    renderLoginPage();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText("Email"), "user@example.com");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Enter your password.");
  });

  it("submits valid credentials to the login endpoint", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (url: string | URL | Request) => {
      const href = String(url);
      if (href.endsWith("/auth/login")) {
        return new Response(JSON.stringify({ access_token: "tok123", token_type: "bearer" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (href.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({ id: 1, email: "user@example.com", created_at: "2026-01-01T00:00:00Z" }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      throw new Error(`Unexpected fetch to ${href}`);
    });

    renderLoginPage();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText("Email"), "user@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/auth/login"),
        expect.objectContaining({ method: "POST" }),
      );
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows an error message when the backend rejects the credentials", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Invalid email or password" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );

    renderLoginPage();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText("Email"), "user@example.com");
    await user.type(screen.getByLabelText("Password"), "wrongpassword");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password.");
  });

  it("calls onSwitchToRegister when the create-account link is clicked", async () => {
    const { onSwitchToRegister } = renderLoginPage();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Create one" }));

    expect(onSwitchToRegister).toHaveBeenCalledTimes(1);
  });
});
