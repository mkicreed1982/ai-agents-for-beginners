/* ============================================================
   AI Agents for Beginners — Interactive Landing Page
   Vanilla JS, no dependencies. Progress persists in localStorage.
   ============================================================ */

(() => {
  "use strict";

  /* ---------- Lesson data (mirrors README curriculum) ---------- */
  const LESSONS = [
    { n: 1,  track: "foundations", title: "Intro to AI Agents & Use Cases", desc: "What agents are, where they shine, and real-world use cases.", path: "../01-intro-to-ai-agents/README.md", video: "https://youtu.be/3zgm60bXmQk" },
    { n: 2,  track: "foundations", title: "Exploring Agentic Frameworks", desc: "Survey the frameworks used to build modern AI agents.", path: "../02-explore-agentic-frameworks/README.md", video: "https://youtu.be/ODwF-EZo_O8" },
    { n: 3,  track: "patterns", title: "Agentic Design Patterns", desc: "The core design principles behind reliable agents.", path: "../03-agentic-design-patterns/README.md", video: "https://youtu.be/m9lM8qqoOEA" },
    { n: 4,  track: "patterns", title: "Tool Use Design Pattern", desc: "Give agents superpowers by letting them call tools & APIs.", path: "../04-tool-use/README.md", video: "https://youtu.be/vieRiPRx-gI" },
    { n: 5,  track: "advanced", title: "Agentic RAG", desc: "Retrieval-augmented generation driven by agent reasoning.", path: "../05-agentic-rag/README.md", video: "https://youtu.be/WcjAARvdL7I" },
    { n: 6,  track: "patterns", title: "Building Trustworthy Agents", desc: "Safety, guardrails, and earning user trust.", path: "../06-building-trustworthy-agents/README.md", video: "https://youtu.be/iZKkMEGBCUQ" },
    { n: 7,  track: "patterns", title: "Planning Design Pattern", desc: "Decompose goals into ordered, achievable steps.", path: "../07-planning-design/README.md", video: "https://youtu.be/kPfJ2BrBCMY" },
    { n: 8,  track: "patterns", title: "Multi-Agent Design Pattern", desc: "Coordinate teams of agents to solve bigger problems.", path: "../08-multi-agent/README.md", video: "https://youtu.be/V6HpE9hZEx0" },
    { n: 9,  track: "advanced", title: "Metacognition Design Pattern", desc: "Agents that reason about their own reasoning.", path: "../09-metacognition/README.md", video: "https://youtu.be/His9R6gw6Ec" },
    { n: 10, track: "production", title: "AI Agents in Production", desc: "Take agents from prototype to real deployment.", path: "../10-ai-agents-production/README.md", video: "https://youtu.be/l4TP6IyJxmQ" },
    { n: 11, track: "advanced", title: "Agentic Protocols (MCP, A2A, NLWeb)", desc: "Standards that let agents talk to tools & each other.", path: "../11-agentic-protocols/README.md", video: "https://youtu.be/X-Dh9R3Opn8" },
    { n: 12, track: "advanced", title: "Context Engineering", desc: "Feed agents the right context at the right time.", path: "../12-context-engineering/README.md", video: "https://youtu.be/F5zqRV7gEag" },
    { n: 13, track: "advanced", title: "Managing Agentic Memory", desc: "Short- and long-term memory for stateful agents.", path: "../13-agent-memory/README.md", video: "https://youtu.be/QrYbHesIxpw" },
    { n: 14, track: "foundations", title: "Microsoft Agent Framework", desc: "Build agents with Microsoft's Agent Framework (MAF).", path: "../14-microsoft-agent-framework/README.md", video: "" },
    { n: 15, track: "advanced", title: "Computer Use Agents (CUA)", desc: "Agents that drive a browser and use a computer.", path: "../15-browser-use/README.md", video: "" },
    { n: 18, track: "production", title: "Securing AI Agents", desc: "Threat models and defenses for agentic systems.", path: "../18-securing-ai-agents/README.md", video: "" },
  ];

  const STORE_KEY = "aafb-progress-v1";
  const THEME_KEY = "aafb-theme";

  /* ---------- Progress state ---------- */
  const loadDone = () => {
    try { return new Set(JSON.parse(localStorage.getItem(STORE_KEY)) || []); }
    catch { return new Set(); }
  };
  const saveDone = (set) => {
    try { localStorage.setItem(STORE_KEY, JSON.stringify([...set])); } catch {}
  };
  let done = loadDone();

  /* ---------- DOM refs ---------- */
  const grid = document.getElementById("lesson-grid");
  const emptyState = document.getElementById("empty-state");
  const searchEl = document.getElementById("search");
  const filtersEl = document.getElementById("filters");
  const fill = document.getElementById("progress-fill");
  const pctEl = document.getElementById("progress-pct");
  const labelEl = document.getElementById("progress-label");

  let activeFilter = "all";
  let query = "";

  /* ---------- Render lessons ---------- */
  function render() {
    const q = query.trim().toLowerCase();
    const visible = LESSONS.filter((l) => {
      const matchFilter = activeFilter === "all" || l.track === activeFilter;
      const matchQuery = !q || (l.title + " " + l.desc + " " + l.track).toLowerCase().includes(q);
      return matchFilter && matchQuery;
    });

    grid.innerHTML = "";
    visible.forEach((l, i) => {
      const isDone = done.has(l.n);
      const card = document.createElement("article");
      card.className = "lesson-card" + (isDone ? " done" : "");
      card.style.animationDelay = `${i * 40}ms`;
      card.innerHTML = `
        <div class="lc-top">
          <div class="lc-num">${l.n}</div>
          <span class="lc-track">${l.track}</span>
        </div>
        <h3>${l.title}</h3>
        <p>${l.desc}</p>
        <div class="lc-actions">
          <a class="lc-link" href="${l.path}">Read lesson</a>
          ${l.video ? `<a class="lc-link" href="${l.video}" target="_blank" rel="noopener">▶ Video</a>` : ""}
          <span class="lc-toggle"><span class="lc-check">${isDone ? "✓" : ""}</span> ${isDone ? "Completed" : "Mark done"}</span>
        </div>`;

      // Toggle completion when clicking the card (but not its links)
      card.addEventListener("click", (e) => {
        if (e.target.closest("a")) return;
        if (done.has(l.n)) done.delete(l.n); else done.add(l.n);
        saveDone(done);
        render();
        updateProgress();
      });
      grid.appendChild(card);
    });

    emptyState.hidden = visible.length !== 0;
  }

  /* ---------- Progress bar ---------- */
  function updateProgress() {
    const total = LESSONS.length;
    const count = LESSONS.filter((l) => done.has(l.n)).length;
    const pct = Math.round((count / total) * 100);
    fill.style.width = pct + "%";
    pctEl.textContent = pct + "% complete";
    labelEl.textContent = `${count} / ${total} lessons`;
  }

  document.getElementById("reset-progress").addEventListener("click", () => {
    done = new Set();
    saveDone(done);
    render();
    updateProgress();
  });

  /* ---------- Search & filters ---------- */
  searchEl.addEventListener("input", (e) => { query = e.target.value; render(); });
  filtersEl.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    filtersEl.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    activeFilter = chip.dataset.filter;
    render();
  });

  /* ---------- Theme toggle ---------- */
  const themeToggle = document.getElementById("theme-toggle");
  const themeIcon = themeToggle.querySelector(".theme-icon");
  function applyTheme(t) {
    document.documentElement.setAttribute("data-theme", t);
    themeIcon.textContent = t === "dark" ? "🌙" : "☀️";
    try { localStorage.setItem(THEME_KEY, t); } catch {}
  }
  applyTheme(localStorage.getItem(THEME_KEY) || "dark");
  themeToggle.addEventListener("click", () => {
    const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    applyTheme(next);
  });

  /* ---------- Scroll progress + reveal ---------- */
  const scrollBar = document.getElementById("scroll-progress");
  window.addEventListener("scroll", () => {
    const h = document.documentElement.scrollHeight - window.innerHeight;
    scrollBar.style.width = (h > 0 ? (window.scrollY / h) * 100 : 0) + "%";
  }, { passive: true });

  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
  }, { threshold: 0.15 });
  document.querySelectorAll(".reveal").forEach((el) => io.observe(el));

  /* ---------- Animated stat counters ---------- */
  const statObserver = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (!en.isIntersecting) return;
      const el = en.target;
      const target = +el.dataset.count;
      const suffix = el.dataset.suffix || "";
      const dur = 1200; const start = performance.now();
      const tick = (now) => {
        const p = Math.min((now - start) / dur, 1);
        const eased = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(target * eased) + suffix;
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
      statObserver.unobserve(el);
    });
  }, { threshold: 0.5 });
  document.querySelectorAll(".stat-num").forEach((el) => statObserver.observe(el));

  /* ---------- "What is an agent" loop animation ---------- */
  const loopSteps = [...document.querySelectorAll(".loop-step")];
  let loopIdx = 0;
  setInterval(() => {
    loopSteps.forEach((s) => s.classList.remove("active"));
    loopSteps[loopIdx % loopSteps.length]?.classList.add("active");
    loopIdx++;
  }, 1400);

  /* ---------- Agent playground simulation ---------- */
  const consoleEl = document.getElementById("console");
  const goalEl = document.getElementById("goal");
  const runBtn = document.getElementById("run-agent");
  document.querySelectorAll(".pg-quick .chip").forEach((c) =>
    c.addEventListener("click", () => { goalEl.value = c.dataset.goal; }));

  const TOOLS = ["web_search", "calculator", "calendar", "code_runner", "memory_store", "summarizer", "file_reader"];
  let running = false;

  function line(text, cls = "") {
    const div = document.createElement("div");
    div.className = "console-line" + (cls ? " " + cls : "");
    div.innerHTML = text;
    consoleEl.appendChild(div);
    consoleEl.scrollTop = consoleEl.scrollHeight;
    return div;
  }
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));

  async function typeLine(text, cls = "") {
    const div = line("", cls);
    div.classList.add("cursor");
    for (let i = 0; i < text.length; i++) {
      div.innerHTML = text.slice(0, i + 1);
      await wait(12);
    }
    div.classList.remove("cursor");
    consoleEl.scrollTop = consoleEl.scrollHeight;
  }

  async function runAgent() {
    if (running) return;
    running = true;
    runBtn.disabled = true;
    runBtn.textContent = "⏳ Thinking…";
    consoleEl.innerHTML = "";

    const goal = (goalEl.value || "Help the user").trim();
    await typeLine(`<span class="tag">[goal]</span> ${escapeHtml(goal)}`);
    await wait(300);

    const steps = 3 + Math.floor(Math.random() * 2);
    for (let i = 1; i <= steps; i++) {
      await typeLine(`<span class="think">[reason]</span> Step ${i}: deciding what to do next…`, "");
      await wait(250);
      const tool = TOOLS[Math.floor(Math.random() * TOOLS.length)];
      await typeLine(`<span class="act">[act]</span> calling tool → <b>${tool}()</b>`, "");
      await wait(350);
      line(`<span class="tag">[observe]</span> ${tool} returned results ✓`, "");
      await wait(250);
    }

    await typeLine(`<span class="done">[done]</span> Goal achieved after ${steps} reasoning steps.`, "done");
    line(`<span class="muted">// This is an illustrative simulation of the perceive → reason → act → reflect loop.</span>`, "muted");

    running = false;
    runBtn.disabled = false;
    runBtn.textContent = "▶ Run agent";
  }
  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
  runBtn.addEventListener("click", runAgent);

  /* ---------- Particle background ---------- */
  const canvas = document.getElementById("bg-canvas");
  const ctx = canvas.getContext("2d");
  let particles = [];
  let W, H;
  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
    const count = Math.min(70, Math.floor(W / 22));
    particles = Array.from({ length: count }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 1.8 + 0.6,
    }));
  }
  function draw() {
    ctx.clearRect(0, 0, W, H);
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > W) p.vx *= -1;
      if (p.y < 0 || p.y > H) p.vy *= -1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(124,92,255,0.55)";
      ctx.fill();
      for (let j = i + 1; j < particles.length; j++) {
        const q = particles[j];
        const d = Math.hypot(p.x - q.x, p.y - q.y);
        if (d < 130) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y);
          ctx.strokeStyle = `rgba(34,211,238,${0.12 * (1 - d / 130)})`;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  }
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    window.addEventListener("resize", resize);
    resize();
    draw();
  }

  /* ---------- Init ---------- */
  render();
  updateProgress();
})();
