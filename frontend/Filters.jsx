import React from "react";

const TABS = [
  { value: "", label: "All" },
  { value: "todo", label: "To do" },
  { value: "in_progress", label: "In progress" },
  { value: "done", label: "Done" },
];

export default function Filters({ status, onStatus, query, onQuery, total }) {
  return (
    <div className="filters">
      <div className="filters__tabs" role="tablist" aria-label="Filter by status">
        {TABS.map((tab) => (
          <button
            key={tab.value || "all"}
            type="button"
            role="tab"
            aria-selected={status === tab.value}
            className={`chip ${status === tab.value ? "is-active" : ""}`}
            onClick={() => onStatus(tab.value)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <input
        className="filters__search"
        type="search"
        placeholder="Search titles"
        value={query}
        onChange={(event) => onQuery(event.target.value)}
        aria-label="Search tasks"
      />

      <span className="filters__count">{total} shown</span>
    </div>
  );
}
