import { useEffect, useState } from "react";
import { api, tokenStore } from "./api.js";
import Login from "./components/Login.jsx";
import TaskBoard from "./components/TaskBoard.jsx";

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tokenStore.get()) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false));
  }, []);

  function handleLogout() {
    tokenStore.clear();
    setUser(null);
  }

  if (loading) {
    return <div className="center muted">Loading…</div>;
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">✓</span> TaskFlow
        </div>
        {user && (
          <div className="userbox">
            <span className="muted">{user.email}</span>
            <button className="btn ghost" onClick={handleLogout}>
              Log out
            </button>
          </div>
        )}
      </header>

      <main className="content">
        {user ? <TaskBoard /> : <Login onAuthed={setUser} />}
      </main>
    </div>
  );
}
