import { LoginForm } from "../features/auth/LoginForm";

export function LoginPage() {
  return (
    <div style={{ padding: "1.2em", maxWidth: 360, margin: "10svh auto 0" }}>
      <h1 style={{ fontSize: "1.4em", textAlign: "center" }}>Vent</h1>
      <LoginForm />
    </div>
  );
}
