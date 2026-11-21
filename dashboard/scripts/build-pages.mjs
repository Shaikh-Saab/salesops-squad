// Cross-platform (Windows + macOS) build for GitHub Pages: sets the /<repo>/ base path.
import { build } from 'vite';
process.env.VITE_BASE = process.env.VITE_BASE || '/salesops-squad/';
await build();
