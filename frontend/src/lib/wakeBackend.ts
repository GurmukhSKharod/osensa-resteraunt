// src/lib/wakeBackend.ts
let alreadyKicked = false;
let lastKick = 0;

export function wakeBackend(
  url?: string,
  { attempts = 2, delayMs = 800, minIntervalMs = 5 * 60_000 } = {}
) {
  const now = Date.now();
  if (alreadyKicked && now - lastKick < minIntervalMs) return;

  alreadyKicked = true;
  lastKick = now;

  const target =
    url ??
    import.meta.env.VITE_BACKEND_HEALTH_URL ??
    "https://osensa-resteraunt-backend.onrender.com/health";

  const pingOnce = () => {
    if ("sendBeacon" in navigator) {
      try {
        navigator.sendBeacon(target);
        return Promise.resolve();
      } catch {}
    }
    return fetch(target, { method: "GET", mode: "no-cors", cache: "no-store" })
      .catch(() => { });
  };

  (async () => {
    await pingOnce();
    for (let i = 1; i < attempts; i++) {
      await new Promise(r => setTimeout(r, delayMs));
      await pingOnce();
    }
  })();
}
