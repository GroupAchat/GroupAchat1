import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import Console from "@/App";
import "@commun/index.css";

const themeEnregistre = localStorage.getItem("ga-theme");
if (themeEnregistre === "clair") document.documentElement.dataset.theme = "light";
if (themeEnregistre === "sombre") document.documentElement.dataset.theme = "dark";

createRoot(document.getElementById("racine")!).render(
  <StrictMode>
    <Console />
  </StrictMode>,
);
