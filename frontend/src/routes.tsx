import { createBrowserRouter, Navigate } from "react-router-dom";
import RootLayout from "./layouts/RootLayout";
import HomePage from "./pages/HomePage";
import LobbyPage from "./pages/LobbyPage";
import GamePage from "./pages/GamePage";
import DeadPage from "./pages/DeadPage";
import GameOverPage from "./pages/GameOverPage";
import MyGamesPage from "./pages/MyGamesPage";

const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      { path: "/", element: <HomePage /> },
      { path: "/my-games", element: <MyGamesPage /> },
      { path: "/game/:code", element: <LobbyPage /> },
      { path: "/game/:code/play", element: <GamePage /> },
      { path: "/game/:code/dead", element: <DeadPage /> },
      { path: "/game/:code/over", element: <GameOverPage /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);

export default router;
