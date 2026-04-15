/*
  Cloudflare Worker — Telegram API Mirror
  ────────────────────────────────────────
  Pakistan mein Telegram blocked hai, yeh worker proxy ka kaam karta hai.

  Deploy Steps:
  1. Go to https://dash.cloudflare.com → Workers & Pages → Create Worker
  2. Paste this code → Deploy
  3. Copy the worker URL (e.g. https://tg-mirror.your-name.workers.dev)
  4. Set in .env: TELEGRAM_API_BASE_URL=https://tg-mirror.your-name.workers.dev

  That's it! All Telegram API calls will route through Cloudflare (not blocked).
*/

export default {
  async fetch(request) {
    const url = new URL(request.url);

    // Rewrite to Telegram API
    const telegramUrl = `https://api.telegram.org${url.pathname}${url.search}`;

    // Forward the request
    const modifiedRequest = new Request(telegramUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });

    // Add CORS headers for browser access (optional)
    const response = await fetch(modifiedRequest);
    const newResponse = new Response(response.body, response);
    newResponse.headers.set('Access-Control-Allow-Origin', '*');

    return newResponse;
  },
};
