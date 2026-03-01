// Root layout with floating account button and global auth modal

import { Outlet } from "react-router-dom";
import AccountButton from "../components/AccountButton";
import AuthModal from "../components/AuthModal";
import { useAuth } from "../context/AuthContext";

export default function RootLayout() {
  const { showAuthModal, closeAuthModal } = useAuth();

  return (
    <>
      <header className="fixed top-0 right-0 z-40 p-3">
        <AccountButton />
      </header>
      <Outlet />
      <AuthModal isOpen={showAuthModal} onClose={closeAuthModal} />
    </>
  );
}
