import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../api/AuthContext";

export function Layout() {
  const { logout, userEmail } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="app-shell">
      <nav className="navbar">
        <Link to="/documents" className="navbar-brand">
          Pricing Calculator
        </Link>
        <div className="navbar-links">
          <Link to="/documents">Documents</Link>
          <Link to="/reports">Reports</Link>
          {userEmail && (
            <div className="navbar-profile">
              <span className="navbar-avatar">{userEmail[0].toUpperCase()}</span>
              <span>{userEmail}</span>
            </div>
          )}
          <button className="link-button" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </nav>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
