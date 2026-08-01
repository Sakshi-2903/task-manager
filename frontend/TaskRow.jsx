import React, { useState } from "react";

import StatusTrack from "./StatusTrack.jsx";

const dateFormat = new Intl.DateTimeFormat(undefined, {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});

function formatDue(iso) {
  return dateFormat.format(new Date(iso));
}

export default function TaskRow({ task, onUpdate, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(task.title);
  const [busy, setBusy] = useState(false);

  const overdue = task.due_date && task.status !== "done" && new Date(task.due_date) < new Date();

  async function run(action) {
    setBusy(true);
    try {
      await action();
    } finally {
      setBusy(false);
    }
  }

  function saveTitle() {
    const title = draft.trim();
    setEditing(false);
    if (!title || title === task.title) {
      setDraft(task.title);
      return;
    }
    run(() => onUpdate(task.id, { title }));
  }

  return (
    <li className={`row ${busy ? "is-busy" : ""}`} data-priority={task.priority}>
      <span className="row__spine" aria-hidden="true" />

      <div className="row__main">
        {editing ? (
          <input
            className="row__edit"
            value={draft}
            autoFocus
            onChange={(event) => setDraft(event.target.value)}
            onBlur={saveTitle}
            onKeyDown={(event) => {
              if (event.key === "Enter") saveTitle();
              if (event.key === "Escape") {
                setDraft(task.title);
                setEditing(false);
              }
            }}
          />
        ) : (
          <button
            type="button"
            className={`row__title ${task.status === "done" ? "is-done" : ""}`}
            onClick={() => setEditing(true)}
            title="Rename"
          >
            {task.title}
          </button>
        )}

        <div className="row__meta">
          <span className="tag">{task.priority}</span>
          {task.due_date && (
            <span className={`tag ${overdue ? "tag--flag" : ""}`}>
              {overdue ? "overdue " : "due "}
              {formatDue(task.due_date)}
            </span>
          )}
        </div>
      </div>

      <StatusTrack
        value={task.status}
        busy={busy}
        onChange={(status) => run(() => onUpdate(task.id, { status }))}
      />

      <button
        type="button"
        className="row__delete"
        disabled={busy}
        aria-label={`Delete ${task.title}`}
        onClick={() => run(() => onDelete(task.id))}
      >
        &#215;
      </button>
    </li>
  );
}
