import { defineConfig } from 'vite';
import QRCode from 'qrcode';

// Prints a QR code for the LAN URL so a phone on the same Wi-Fi can scan it.
function lanQr() {
  const print = (server) => {
    server.httpServer?.once('listening', () => {
      setTimeout(async () => {
        const url = server.resolvedUrls?.network?.[0];
        if (!url) {
          console.log('\n  No local network address found (are you on Wi-Fi?). QR skipped.\n');
          return;
        }
        const qr = await QRCode.toString(url, { type: 'terminal', small: true });
        console.log(`\n  Scan to open on your phone (same Wi-Fi): ${url}\n\n${qr}`);
      }, 200);
    });
  };
  return { name: 'lan-qr', configureServer: print, configurePreviewServer: print };
}

export default defineConfig({
  // GitHub Pages serves the site at /<repo>/. The deploy workflow sets VITE_BASE.
  base: process.env.VITE_BASE || '/',
  envDir: '..', // read the repo-root .env (VITE_* variables only)
  server: { host: true, port: 5173 },
  preview: { host: true, port: 4173 },
  plugins: [lanQr()],
});
