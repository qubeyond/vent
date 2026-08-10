import { apiFetch, setToken } from "../../shared/api/client";

export async function login(username: string, password: string): Promise<void> {
  const response = await apiFetch<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  setToken(response.access_token);
}

export async function fetchMe(): Promise<{ username: string }> {
  return apiFetch("/auth/me");
}
