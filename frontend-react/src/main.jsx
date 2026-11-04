import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import AuthApplication from "./AuthApplication.jsx";
import { AuthProvider } from "./auth/context/AuthContext.jsx";
import "./styles.css";
import "./compact.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <AuthApplication />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
import "./refinement.css";

import "./auth.css";
