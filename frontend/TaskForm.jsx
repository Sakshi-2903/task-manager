import React, { useState } from "react";

const EMPTY = { title: "", priority: "medium", due: "" };

export default function TaskForm({ onCreate, fieldErrors }) {
  const [form, setForm] = useState(EMPTY);
  const [busy, setBusy] = useState(false);

  const set = (key) => (event) => setForm({ ...form, [key]: event.target.value });

  async function submit(event) {
    event.preventDefault();
    if (!form.title.trim() || busy) return;

    setBusy(true);
    try {
      const payload = { title: form.title.trim(), priority: form.priority };
      if (form.due) payload.due_date = new Date(form.due).toISOString();
      await onCreate(payload);
      setForm(EMPTY);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="compose" onSubmit={submit}>
      <input
        className="compose__title"
        placeholder="What needs doing?"
        value={form.title}
        onChange={set("title")}
        aria-label="Task title"
        aria-invalid={Boolean(fieldErrors.title)}
        maxLength={200}
      />

      <select
        className="compose__field"
        value={form.priority}
        onChange={set("priority")}
        aria-label="Priority"
      >
        <option value="low">Low</option>
        <option value="medium">Medium</option>
        <option value="high">High</option>
      </select>

      <input
        className="compose__field"
        type="datetime-local"
        value={form.due}
        onChange={set("due")}
        aria-label="Due date"
      />

      <button className="compose__submit" type="submit" disabled={busy || !form.title.trim()}>
        {busy ? "Adding" : "Add task"}
      </button>

      {fieldErrors.title && <p className="compose__error">{fieldErrors.title}</p>}
    </form>
  );
}
