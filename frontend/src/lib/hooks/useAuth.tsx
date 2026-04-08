"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { onAuthStateChanged, User } from "firebase/auth";
import { auth } from "../firebase";
import axios from "axios";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  heliXUser: any | null;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  heliXUser: null,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [heliXUser, setHeliXUser] = useState<any | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setUser(firebaseUser);
      
      if (firebaseUser) {
        // Exchange Firebase token with our backend to get/create user profile
        try {
          const idToken = await firebaseUser.getIdToken();
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
          const response = await axios.post(`${apiUrl}/api/auth/verify`, {
            idToken,
          });
          setHeliXUser(response.data);
        } catch (error) {
          console.error("Failed to verify user with backend:", error);
        }
      } else {
        setHeliXUser(null);
      }
      
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, heliXUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
