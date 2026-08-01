const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:5001";

class ApiError extends Error {
  constructor(message, status, details) {
    super(message);
    this.status = status;
    this.details = details || {};
  }
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new ApiError("Can't reach the API. Is the backend running?", 0);
  }

  if (response.status === 204) return null;

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const error = body?.error ?? {};
    throw new ApiError(error.message || "Something went wrong", response.status, error.details);
  }
  return body;
}

const listTasks = ({ status, q, page = 1, limit = 20 } = {}) => {
  const params = new URLSearchParams({ page, limit });
  if (status) params.set("status", status);
  if (q) params.set("q", q);
  return request(`/api/tasks?${params}`);
};

const createTask = (task) =>
  request("/api/tasks", { method: "POST", body: JSON.stringify(task) });

const updateTask = (id, changes) =>
  request(`/api/tasks/${id}`, { method: "PATCH", body: JSON.stringify(changes) });

const deleteTask = (id) => request(`/api/tasks/${id}`, { method: "DELETE" });

const checkReady = async () => {
  try {
    const response = await fetch(`${BASE}/readyz`);
    return response.ok;
  } catch {
    return false;
  }
};

export { ApiError, checkReady, createTask, deleteTask, listTasks, updateTask };