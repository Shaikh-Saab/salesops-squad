// Generates a QR code PNG for the live dashboard URL.
// Usage: npm run qr:live            (uses the default GitHub Pages URL)
//        npm run qr:live -- <url>   (any other URL)
import QRCode from 'qrcode';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const url = process.argv[2] || 'https://shaikh-saab.github.io/salesops-squad/';
const here = dirname(fileURLToPath(import.meta.url));
const out = resolve(here, '..', '..', 'docs', 'qr-live.png');

await QRCode.toFile(out, url, { width: 512, margin: 2 });
console.log(`QR for ${url}\nwritten to ${out}`);
console.log(await QRCode.toString(url, { type: 'terminal', small: true }));
