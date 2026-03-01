import { createBrowserRouter, Navigate } from "react-router-dom";
import HomePage from "./pages/HomePage";
import LobbyPage from "./pages/LobbyPage";
import GamePage from "./pages/GamePage";
import DeadPage from "./pages/DeadPage";
import GameOverPage from "./pages/GameOverPage";

const router = createBrowserRouter([
  { path: "/", element: <HomePage /> },
  { path: "/game/:code", element: <LobbyPage /> },
  { path: "/game/:code/play", element: <GamePage /> },
  { path: "/game/:code/dead", element: <DeadPage /> },
  { path: "/game/:code/over", element: <GameOverPage /> },
  { path: "*", element: <Navigate to="/" replace /> },
]);

export default router;
