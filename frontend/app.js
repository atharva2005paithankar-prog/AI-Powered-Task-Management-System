/* Docket frontend: plain JavaScript, no framework.
   It talks to the FastAPI backend with fetch() and sends the JWT in the
   Authorization header. Text is always added with textContent / text nodes
   (never innerHTML), so task text can't inject HTML into the page. */

const TOKEN_KEY = "docket_token";
const STATUSES = ["Pending", "In Progress", "Testing", "Completed"];

const state = {
  token: localStorage.getItem(TOKEN_KEY),
  user: null,
  tasks: [],
  editingId: null, // null = creating a new task
};

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------- helpers
/** Tiny helper to build DOM elements: h("p", {class: "x"}, "text", childNode) */
function h(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2), value);
    } else if (value !== false && value != null) {
      node.setAttribute(key, value === true ? "" : value);
    }
  }
  for (const child of children.flat()) {
    if (child == null || child === false) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
}

let toastTimer;
function showToast(message, kind = "info") {
  const toast = $("toast");
  toast.textContent = message;
  toast.className = kind === "error" ? "error" : "";
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (toast.hidden = true), 4500);
}

function showFormError(id, message) {
  const box = $(id);
  box.textContent = message || "";
  box.hidden = !message;
}

/** Disable a button and change its label while a request is running. */
function setBusy(button, busy, busyLabel) {
  if (busy) {
    button.dataset.label = button.textContent;
    button.textContent = busyLabel;
  } else if (button.dataset.label) {
    button.textContent = button.dataset.label;
  }
  button.disabled = busy;
}

function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

// -------------------------------------------------------------------- API
function readError(data, status) {
  if (data && typeof data.detail === "string") return data.detail;
  if (data && Array.isArray(data.detail)) {
    // FastAPI validation errors (422): [{loc: [...], msg: "..."}]
    return data.detail.map((e) => `${e.loc.slice(1).join(".")}: ${e.msg.replace("Value error, ", "")}`).join("; ");
  }
  return `Request failed (${status})`;
}

async function api(path, { method = "GET", body } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (state.token) headers["Authorization"] = `Bearer ${state.token}`;

  let response;
  try {
    response = await fetch(path, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Cannot reach the server. Is it running?");
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    if (response.status === 401 && state.user) {
      signOut();
      throw new Error("Your session expired. Please sign in again.");
    }
    throw new Error(readError(data, response.status));
  }
  return data;
}

// ------------------------------------------------------- sign in / sign up
function showAuthView() {
  $("app-view").hidden = true;
  $("auth-view").hidden = false;
}

function showTab(which) {
  const login = which === "login";
  $("login-form").hidden = !login;
  $("register-form").hidden = login;
  $("tab-login").setAttribute("aria-selected", String(login));
  $("tab-register").setAttribute("aria-selected", String(!login));
}

async function startSession(token, user) {
  state.token = token;
  state.user = user;
  localStorage.setItem(TOKEN_KEY, token);
  showAppView();
  await loadTasks();
}

function signOut() {
  state.token = null;
  state.user = null;
  state.tasks = [];
  localStorage.removeItem(TOKEN_KEY);
  showAuthView();
}

async function handleLogin(event) {
  event.preventDefault();
  showFormError("login-error", "");
  const form = new FormData(event.target);
  const button = event.target.querySelector("button[type=submit]");
  setBusy(button, true, "Signing in...");
  try {
    const result = await api("/api/auth/login", {
      method: "POST",
      body: { email: form.get("email").trim(), password: form.get("password") },
    });
    event.target.reset();
    await startSession(result.access_token, result.user);
  } catch (error) {
    showFormError("login-error", error.message);
  } finally {
    setBusy(button, false);
  }
}

async function handleRegister(event) {
  event.preventDefault();
  showFormError("register-error", "");
  const form = new FormData(event.target);
  const email = form.get("email").trim();
  const password = form.get("password");
  const button = event.target.querySelector("button[type=submit]");
  setBusy(button, true, "Creating account...");
  try {
    await api("/api/auth/register", { method: "POST", body: { name: form.get("name"), email, password } });
    const result = await api("/api/auth/login", { method: "POST", body: { email, password } });
    event.target.reset();
    await startSession(result.access_token, result.user);
  } catch (error) {
    showFormError("register-error", error.message);
  } finally {
    setBusy(button, false);
  }
}

// ------------------------------------------------------------------ board
function showAppView() {
  $("auth-view").hidden = true;
  $("app-view").hidden = false;
  $("user-name").textContent = state.user.name;
  $("user-role").textContent = state.user.role;
  const isAdmin = state.user.role === "admin";
  $("board-title").textContent = isAdmin ? "All tasks" : "Your tasks";
  $("board-subtitle").textContent = isAdmin
    ? "As an admin you can edit every task and change its status."
    : "You can create and edit your own tasks. An admin updates their status.";
}

async function loadTasks() {
  try {
    state.tasks = await api("/api/tasks?limit=100");
    renderBoard();
  } catch (error) {
    showToast(error.message, "error");
  }
}

function renderBoard() {
  const board = $("board");
  board.replaceChildren();
  for (const status of STATUSES) {
    const tasks = state.tasks.filter((task) => task.status === status);
    board.append(
      h(
        "section",
        { class: "column", "data-status": status },
        h("header", { class: "column-head" }, h("h2", {}, status), h("span", { class: "count" }, tasks.length)),
        tasks.length ? tasks.map(buildCard) : h("p", { class: "empty" }, `No tasks in ${status}.`)
      )
    );
  }
}

function buildCard(task) {
  const isAdmin = state.user.role === "admin";
  const summaryBox = h("div", { class: "summary", hidden: true });

  const summarizeButton = h("button", { type: "button", class: "btn btn-ai btn-small" }, "Summarize with AI");
  summarizeButton.addEventListener("click", () => summarizeTask(task, summarizeButton, summaryBox));

  const actions = h(
    "div",
    { class: "card-actions" },
    h("button", { type: "button", class: "btn btn-quiet btn-small", onclick: () => openDialog(task) }, "Edit"),
    summarizeButton
  );

  // Only admins get the status control (the API also enforces this with a 403).
  if (isAdmin) {
    const select = h(
      "select",
      { class: "status-select", "aria-label": `Status for ${task.title}` },
      STATUSES.map((status) => h("option", { value: status, selected: status === task.status }, status))
    );
    select.addEventListener("change", () => changeStatus(task, select.value));
    actions.append(select);
  }

  const ownerText = isAdmin ? `${task.owner.name}, ` : "";
  return h(
    "article",
    { class: "card" },
    h("h3", {}, task.title),
    task.description ? h("p", { class: "card-text" }, task.description) : null,
    h("p", { class: "card-meta" }, `${ownerText}created ${formatDate(task.created_at)}`),
    actions,
    summaryBox
  );
}

async function changeStatus(task, newStatus) {
  try {
    const updated = await api(`/api/tasks/${task.id}/status`, { method: "PATCH", body: { status: newStatus } });
    state.tasks = state.tasks.map((item) => (item.id === updated.id ? updated : item));
    showToast(`Moved to ${updated.status}.`);
  } catch (error) {
    showToast(error.message, "error");
  }
  renderBoard(); // redraw either way, so the select always shows the real status
}

// ------------------------------------------------------- AI: summarise task
async function summarizeTask(task, button, box) {
  setBusy(button, true, "Summarizing...");
  try {
    const result = await api(`/api/tasks/${task.id}/summarize`, { method: "POST" });
    box.replaceChildren(
      h("p", {}, result.summary),
      h("ul", {}, result.key_points.map((point) => h("li", {}, point))),
      h("p", { class: "summary-meta" }, `AI summary from ${result.provider} (${result.model})`)
    );
    box.hidden = false;
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    setBusy(button, false);
  }
}

// ----------------------------------------------- create / edit task dialog
function openDialog(task = null) {
  state.editingId = task ? task.id : null;
  $("dialog-title").textContent = task ? "Edit task" : "New task";
  $("task-title").value = task ? task.title : "";
  $("task-description").value = task && task.description ? task.description : "";
  showFormError("task-error", "");
  $("task-dialog").showModal();
  $("task-title").focus();
}

async function saveTask(event) {
  event.preventDefault();
  showFormError("task-error", "");
  const title = $("task-title").value.trim();
  const description = $("task-description").value.trim();
  const button = $("save-btn");

  setBusy(button, true, "Saving...");
  try {
    const body = { title, description: description || null };
    if (state.editingId) {
      await api(`/api/tasks/${state.editingId}`, { method: "PUT", body });
    } else {
      await api("/api/tasks", { method: "POST", body });
    }
    $("task-dialog").close();
    showToast(state.editingId ? "Task updated." : "Task created.");
    await loadTasks();
  } catch (error) {
    showFormError("task-error", error.message);
  } finally {
    setBusy(button, false);
  }
}

// -------------------------------------------- AI: draft description (Option A)
async function draftDescription() {
  const title = $("task-title").value.trim();
  const field = $("task-description");
  const button = $("ai-draft-btn");

  if (title.length < 3) {
    showFormError("task-error", "Type a title (at least 3 characters) so the AI knows what to write about.");
    return;
  }
  if (field.value.trim() && !confirm("Replace the current description with an AI draft?")) return;

  showFormError("task-error", "");
  setBusy(button, true, "Drafting...");
  try {
    const result = await api("/api/tasks/generate-description", { method: "POST", body: { title } });
    const checklist = result.checklist.map((step) => `- ${step}`).join("\n");
    field.value = `${result.description}\n\nChecklist:\n${checklist}`;
  } catch (error) {
    showFormError("task-error", error.message);
  } finally {
    setBusy(button, false);
  }
}

// ---------------------------------------------------------------- start up
function wireEvents() {
  $("tab-login").addEventListener("click", () => showTab("login"));
  $("tab-register").addEventListener("click", () => showTab("register"));
  $("login-form").addEventListener("submit", handleLogin);
  $("register-form").addEventListener("submit", handleRegister);
  $("logout-btn").addEventListener("click", signOut);
  $("new-task-btn").addEventListener("click", () => openDialog());
  $("cancel-btn").addEventListener("click", () => $("task-dialog").close());
  $("task-form").addEventListener("submit", saveTask);
  $("ai-draft-btn").addEventListener("click", draftDescription);

  // "Fill admin" / "Fill user" buttons put the seeded test credentials in the form.
  document.querySelectorAll("[data-fill]").forEach((button) => {
    button.addEventListener("click", () => {
      const [email, password] = button.dataset.fill.split("|");
      showTab("login");
      const form = $("login-form");
      form.elements.email.value = email;
      form.elements.password.value = password;
    });
  });
}

async function start() {
  wireEvents();
  if (!state.token) return showAuthView();
  try {
    // Restore the session if the saved token is still valid.
    state.user = await api("/api/auth/me");
    showAppView();
    await loadTasks();
  } catch {
    signOut();
  }
}

start();
