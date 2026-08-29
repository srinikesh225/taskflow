import { useEffect, useState } from "react";
import { api } from "../api.js";
import TaskForm from "./TaskForm.jsx";
import TaskItem from "./TaskItem.jsx";

const FILTERS = [
  { key: "", label: "All" },
  { key: "todo", label: "To do" },
  { key: "in_progress", label: "In progress" },
  { key: "done", label: "Done" },
];

export default function TaskBoard() {
  const [tasks, setTasks] = useState([]);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  async function load(status = filter) {
    setLoading(true);
    setError(null);
    try {
      setTasks(await api.listTasks(status));
    } catch (err) {
      setError(err.detail || err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(filter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  async function handleCreate(task) {
    await api.createTask(task);
    load();
  }

  async function handleUpdate(id, patch) {
    await api.updateTask(id, patch);
    load();
  }

  async function handleDelete(id) {
    await api.deleteTask(id);
    setTasks((ts) => ts.filter((t) => t.id !== id));
  }

  return (
    <div className="board">
      <TaskForm onCreate={handleCreate} />

      <div className="toolbar">
        <div className="filters">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              className={`chip ${filter === f.key ? "active" : ""}`}
              onClick={() => setFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
        <span className="muted count">{tasks.length} task(s)</span>
      </div>

      {error && <div className="error">{error}</div>}
      {loading ? (
        <div className="muted center">Loading tasks…</div>
      ) : tasks.length === 0 ? (
        <div className="empty muted">No tasks yet. Add one above.</div>
      ) : (
        <ul className="task-list">
          {tasks.map((t) => (
            <TaskItem
              key={t.id}
              task={t}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
