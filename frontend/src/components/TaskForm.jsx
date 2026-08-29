import { useState } from "react";

export default function TaskForm({ onCreate }) {
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState("medium");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function submit(e) {
    e.preventDefault();
    const trimmed = title.trim();
    if (!trimmed) return;
    setBusy(true);
    setError(null);
    try {
      await onCreate({ title: trimmed, priority });
      setTitle("");
      setPriority("medium");
    } catch (err) {
      setError(err.detail || err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card task-form" onSubmit={submit}>
      <input
        className="grow"
        placeholder="What needs doing?"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        maxLength={200}
        aria-label="Task title"
      />
      <select value={priority} onChange={(e) => setPriority(e.target.value)} aria-label="Priority">
        <option value="low">Low</option>
        <option value="medium">Medium</option>
        <option value="high">High</option>
      </select>
      <button className="btn primary" disabled={busy || !title.trim()} type="submit">
        Add
      </button>
      {error && <div className="error full">{error}</div>}
    </form>
  );
}
