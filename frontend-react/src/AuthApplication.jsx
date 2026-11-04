import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import App from "./App";
import Connexion from "./auth/pages/Connexion";
import Inscription from "./auth/pages/Inscription";
import { useAuth } from "./auth/context/AuthContext";
export default function AuthApplication() {
  const { utilisateur, verification } = useAuth();
  const location = useLocation();
  if (verification)
    return (
      <main className="auth-loading" role="status">
        Vérification de votre session…
      </main>
    );
  if (
    location.pathname === "/connexion" ||
    location.pathname === "/inscription"
  )
    return (
      <Routes>
        <Route path="/connexion" element={<Connexion />} />
        <Route path="/inscription" element={<Inscription />} />
      </Routes>
    );
  if (!utilisateur)
    return (
      <Navigate to="/connexion" replace state={{ depuis: location.pathname }} />
    );
  return <App key={utilisateur.id} />;
}
