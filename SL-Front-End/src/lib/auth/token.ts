const hasDocument = typeof document !== "undefined";
const hasWindow = typeof window !== "undefined";

export const AUTH_TOKEN_COOKIE_KEY = "access_token";
const DEFAULT_MAX_AGE_SECONDS = 60 * 60 * 24 * 7; // 7일

/**
 * access token을 쿠키에 저장합니다.
 */
export function setAuthTokenCookie(
  token: string,
  maxAge = DEFAULT_MAX_AGE_SECONDS,
): void {
  if (!hasDocument) {
    return;
  }

  const secureFlag =
    hasWindow && window.location.protocol === "https:" ? "; Secure" : "";
  const serialized = `${AUTH_TOKEN_COOKIE_KEY}=${encodeURIComponent(token)}; Path=/; Max-Age=${maxAge}; SameSite=Lax${secureFlag}`;

  document.cookie = serialized;
}

/**
 * 쿠키에서 access token을 읽어옵니다.
 */
export function getAuthTokenFromCookie(): string | null {
  if (!hasDocument) {
    return null;
  }

  const tokenCookie = document.cookie
    .split(";")
    .map((cookie) => cookie.trim())
    .find((cookie) => cookie.startsWith(`${AUTH_TOKEN_COOKIE_KEY}=`));

  if (!tokenCookie) {
    return null;
  }

  const [, ...valueParts] = tokenCookie.split("=");
  const value = valueParts.join("=");

  return value ? decodeURIComponent(value) : null;
}

/**
 * access token 쿠키를 제거합니다.
 */
export function clearAuthTokenCookie(): void {
  if (!hasDocument) {
    return;
  }

  document.cookie = `${AUTH_TOKEN_COOKIE_KEY}=; Path=/; Max-Age=0; SameSite=Lax`;
}
