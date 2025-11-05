export async function wakeBackend(
  url?: string,
  { attempts = 3, delayMs = 100 } = {}
) {
  const target =
    url ??
    import.meta.env.VITE_BACKEND_HEALTH_URL ??
    "https://osensa-resteraunt-backend.onrender.com/health";

  const pingOnce = () =>
    fetch(target, { method: "GET", mode: "no-cors", cache: "no-store" })
      .catch(() => {});

  await pingOnce();
  for (let i = 1; i < attempts; i++) {
    await new Promise(r => setTimeout(r, delayMs));
    await pingOnce();
  }
}