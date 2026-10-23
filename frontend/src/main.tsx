import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "@/App";
import "@/index.css";

// Le thème choisi est appliqué avant le premier rendu : lu après, il
// provoquerait un éclair blanc sur un écran réglé en sombre.
const themeEnregistre = localStorage.getItem("ga-theme");
if (themeEnregistre === "clair") document.documentElement.dataset.theme = "light";
if (themeEnregistre === "sombre") document.documentElement.dataset.theme = "dark";

createRoot(document.getElementById("racine")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
