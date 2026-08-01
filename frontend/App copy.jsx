import { useCallback, useEffect, useState } from "react";

import Filters from "./components/Filters.jsx";
import TaskForm from "./components/TaskForm.jsx";
import TaskRow from "./components/TaskRow.jsx";
import * as api from "./api.js";

const LIMIT = 20;

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const [apiReady, setApiReady] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
      setPage(1);
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listTasks({ status, q: debouncedQuery, page, limit: LIMIT });
      setTasks(data.items);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [status, debouncedQuery, page]);

  useEffect(() => {
    load();
  }, [load]);

  // Polls the readiness probe so a rolling deploy is visible in the UI.
  useEffect(() => {
    let active = true;
    const check = async () => {
      const ready = await api.checkReady();
      if (active) setApiReady(ready);
    };
    check();
    const timer = setInterval(check, 10000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);

  async function guard(action) {
    try {
      await action();
      setError(null);
      setFieldErrors({});
    } catch (err) {
      setError(err.message);
      setFieldErrors(err.details || {});
      throw err;
    }
  }

  const create = (task) =>
    guard(async () => {
      await api.createTask(task);
      setPage(1);
      await load();
    });

  const update = (id, changes) =>
    guard(async () => {
      const updated = await api.updateTask(id, changes);
      setTasks((current) => current.map((task) => (task.id === id ? updated : task)));
    });

  const remove = (id) =>
    guard(async () => {
      await api.deleteTask(id);
      await load();
    });

  const pages = Math.max(1, Math.ceil(total / LIMIT));

  return (
    <div className="shell">
      <header className="masthead">
        <h1 className="masthead__title">Tasks</h1>
        <span className={`pulse ${apiReady ? "is-up" : "is-down"}`}>
          <i aria-hidden="true" />
          {apiReady ? "API connected" : "API unreachable"}
        </span>
      </header>

      <TaskForm onCreate={create} fieldErrors={fieldErrors} />

      <Filters
        status={status}
        onStatus={(value) => {
          setStatus(value);
          setPage(1);
        }}
        query={query}
        onQuery={setQuery}
        total={total}
      />

      {error && (
        <p className="banner" role="alert">
          {error}
        </p>
      )}

      {loading && tasks.length === 0 ? (
        <p className="hint">Loading tasks</p>
      ) : tasks.length === 0 ? (
        <p className="hint">
          {debouncedQuery || status
            ? "Nothing matches this filter. Clear it to see everything."
            : "No tasks yet. Add the first one above."}
        </p>
      ) : (
        <ul className="list">
          {tasks.map((task) => (
            <TaskRow key={task.id} task={task} onUpdate={update} onDelete={remove} />
          ))}
        </ul>
      )}

      {pages > 1 && (
        <nav className="pager" aria-label="Pagination">
          <button type="button" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            Previous
          </button>
          <span>
            Page {page} of {pages}
          </span>
          <button type="button" disabled={page >= pages} onClick={() => setPage(page + 1)}>
            Next
          </button>
        </nav>
      )}
    </div>
  );
}
