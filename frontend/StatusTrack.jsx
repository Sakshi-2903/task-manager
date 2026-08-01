import React from "react";

const STAGES = [
  { value: "todo", label: "To do" },
  { value: "in_progress", label: "In progress" },
  { value: "done", label: "Done" },
];

/**
 * The three stages are a rail rather than a dropdown: status is a sequence, so
 * the control shows how far along a task is and lets you move it in one click.
 */
export default function StatusTrack({ value, onChange, busy }) {
  const currentIndex = STAGES.findIndex((stage) => stage.value === value);

  return (
    <div className="track" role="group" aria-label="Status">
      {STAGES.map((stage, index) => (
        <button
          key={stage.value}
          type="button"
          className={[
            "track__seg",
            index <= currentIndex ? "is-filled" : "",
            index === currentIndex ? "is-current" : "",
          ].join(" ")}
          aria-pressed={stage.value === value}
          disabled={busy}
          onClick={() => stage.value !== value && onChange(stage.value)}
        >
          {stage.label}
        </button>
      ))}
    </div>
  );
}
