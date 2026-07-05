"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { authService } from "@/services/AuthService";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const auth = authService.isAuthenticated();
    setIsAuthenticated(auth);
    if (auth) {
      setUser(authService.getCurrentUser());
    }
  }, [pathname]);

  const handleLogout = () => {
    authService.logout();
    setIsAuthenticated(false);
    setUser(null);
    router.push("/login");
  };

  // Don't show nav on auth pages
  if (pathname === "/login" || pathname === "/register" || pathname === "/confirm") {
    return null;
  }

  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">
      <div className="container navbar-inner">
        <Link href="/" className="navbar-logo" aria-label="Student Portal Home">
          🎓 StudentPortal
        </Link>

        <ul className="navbar-links" role="list">
          {isAuthenticated ? (
            <>
              <li>
                <Link
                  href="/profile/view"
                  className="navbar-link"
                  aria-current={pathname === "/profile/view" ? "page" : undefined}
                >
                  My Profile
                </Link>
              </li>
              <li>
                <Link
                  href="/profile/create"
                  className="navbar-link"
                  aria-current={pathname === "/profile/create" ? "page" : undefined}
                >
                  Edit Profile
                </Link>
              </li>
              <li>
                <button
                  onClick={handleLogout}
                  className="btn btn-secondary btn-sm"
                  type="button"
                  aria-label="Log out"
                >
                  Log out
                </button>
              </li>
            </>
          ) : (
            <>
              <li>
                <Link href="/login" className="navbar-link">
                  Sign In
                </Link>
              </li>
              <li>
                <Link href="/register" className="btn btn-primary btn-sm">
                  Get Started
                </Link>
              </li>
            </>
          )}
        </ul>
      </div>
    </nav>
  );
}
