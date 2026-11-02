/**
 * Host uygulama (BuildingFlow, TraceFlow) bağlamı.
 *
 * Host menüsündeki bağlantı şu parametrelerle gelir:
 *   ?idp=<kimlik-sağlayıcı-id>&return=<host-adresi>&locale=tr|en&theme=light|dark&host=<görünen-ad>
 * Dönüş adresi yalnızca NEXT_PUBLIC_AIH_HOST_RETURN_ORIGINS içindeki origin'lerden biriyse kabul edilir
 * (açık yönlendirme / phishing koruması).
 */

export type Locale = 'tr' | 'en';
export type ThemeMode = 'light' | 'dark';

export interface HostContext {
  idp: string | null;
  returnUrl: string | null;
  hostName: string | null;
  locale: Locale | null;
  theme: ThemeMode | null;
}

const STORAGE_KEY = 'aih-host-context';

export function safeReturnUrl(candidate: string | null, allowedOrigins: readonly string[]): string | null {
  if (!candidate) return null;
  try {
    const url = new URL(candidate);
    if (url.protocol !== 'https:' && url.protocol !== 'http:') return null;
    return allowedOrigins.includes(url.origin) ? url.toString() : null;
  } catch {
    return null;
  }
}

export function parseHostContext(search: string, allowedOrigins: readonly string[], knownIdps: readonly string[]): HostContext {
  const params = new URLSearchParams(search);
  const idp = params.get('idp');
  const locale = params.get('locale');
  const theme = params.get('theme');
  const hostName = params.get('host');
  return {
    idp: idp && knownIdps.includes(idp) ? idp : null,
    returnUrl: safeReturnUrl(params.get('return'), allowedOrigins),
    hostName: hostName && /^[\p{L}\p{N} ._-]{1,40}$/u.test(hostName) ? hostName : null,
    locale: locale === 'tr' || locale === 'en' ? locale : null,
    theme: theme === 'light' || theme === 'dark' ? theme : null,
  };
}

export function mergeHostContext(previous: HostContext | null, next: HostContext): HostContext {
  return {
    idp: next.idp ?? previous?.idp ?? null,
    returnUrl: next.returnUrl ?? previous?.returnUrl ?? null,
    hostName: next.hostName ?? previous?.hostName ?? null,
    locale: next.locale ?? previous?.locale ?? null,
    theme: next.theme ?? previous?.theme ?? null,
  };
}

export function loadStoredContext(): HostContext | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as HostContext) : null;
  } catch {
    return null;
  }
}

export function storeContext(context: HostContext): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(context));
  } catch {
    // Depo kapalıysa bağlam yalnızca bu sayfa için geçerli olur.
  }
}
