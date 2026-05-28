# Interactive Learning Hub 🌐

An interactive, dynamic landing page for the **AI Agents for Beginners** course.

![hub](https://img.shields.io/badge/status-live-22C55E) ![deps](https://img.shields.io/badge/dependencies-none-7c5cff)

## ✨ Features

- **Live progress tracking** — click any lesson card to mark it complete; your progress bar fills up and persists in your browser via `localStorage` (nothing is sent anywhere).
- **Searchable, filterable curriculum** — all 16+ lessons, filterable by track (Foundations, Design Patterns, Advanced, Production) with instant search.
- **Interactive agent playground** — type a goal and watch a simulated *perceive → reason → act → reflect* loop run in a live console.
- **Animated "what is an agent" loop**, count-up stats, an interactive particle background, scroll progress, and reveal-on-scroll.
- **Dark / light theme toggle** that remembers your choice.
- **Fully responsive** and respects `prefers-reduced-motion`.

Built with plain HTML, CSS, and vanilla JavaScript — **zero build step and no dependencies**.

## 🚀 Run it locally

From the repository root:

```bash
# Python
python -m http.server 8000
# then open http://localhost:8000/docs/

# …or Node
npx serve .
```

You can also just open `docs/index.html` directly in a browser.

## 🌍 Publish with GitHub Pages

In the repo settings → **Pages**, set the source to the `main` branch and the
`/docs` folder. The page is then served at `https://<owner>.github.io/ai-agents-for-beginners/`.

## 📁 Files

| File | Purpose |
|------|---------|
| `index.html` | Page structure & content |
| `styles.css` | Theming, layout, animations |
| `app.js` | Lesson data, progress tracking, search/filter, playground, particles |

The lesson links point at the course READMEs one level up (e.g. `../01-intro-to-ai-agents/README.md`).
