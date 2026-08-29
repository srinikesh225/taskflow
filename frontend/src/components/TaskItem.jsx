const STATUS_LABELS = {
  todo: "To do",
  in_progress: "In progress",
  done: "Done",
};
const NEXT_STATUS = { todo: "in_progress", in_progress: "done", done: "todo" };

export default function TaskItem({ task, onUpdate, onDelete }) {
  return (
    <li className={`task ${task.status} prio-${task.priority}`}>
      <button
        className="status-toggle"
        title="Cycle status"
        onClick={() => onUpdate(task.id, { status: NEXT_STATUS[task.status] })}
      >
        <span className={`badge ${task.status}`}>{STATUS_LABELS[task.status]}</span>
      </button>

      <div className="task-main">
        <span className={`task-title ${task.status === "done" ? "struck" : ""}`}>
          {task.title}
        </span>
        {task.description && <span className="task-desc muted">{task.description}</span>}
      </div>

      <span className={`prio-tag ${task.priority}`}>{task.priority}</span>

      <button
        className="btn ghost danger"
        title="Delete task"
        onClick={() => onDelete(task.id)}
      >
        ✕
      </button>
    </li>
  );
}
