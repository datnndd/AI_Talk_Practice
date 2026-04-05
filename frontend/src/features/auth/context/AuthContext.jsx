import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { httpClient } from "@/shared/api/httpClient";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("access_token"));
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setToken(null);
    setUser(null);
  }, []);

  const fetchUser = useCallback(async () => {
    try {
      const response = await httpClient.get("/auth/me");
      setUser(response.data);
    } catch (error) {
      console.error("Failed to fetch user", error);
      logout();
    } finally {
      setIsLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    if (token) {
      fetchUser();
    } else {
      setIsLoading(false);
    }
  }, [token, fetchUser]);

  const login = async (email, password) => {
    const response = await httpClient.post("/auth/login", { email, password });
    const { access_token, refresh_token } = response.data;
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    setToken(access_token);
    return response.data;
  };

  const googleLogin = async (idToken) => {
    const response = await httpClient.post("/auth/google", { id_token: idToken });
    const { access_token, refresh_token } = response.data;
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    setToken(access_token);
    return response.data;
  };

  const register = async (userData) => {
    const response = await httpClient.post("/auth/register", userData);
    const { access_token, refresh_token } = response.data;
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    setToken(access_token);
    return response.data;
  };

  const onboard = async (onboardingData) => {
    const response = await httpClient.put("/auth/me/onboard", onboardingData);
    setUser(response.data);
    return response.data;
  };

  return (
    <AuthContext.Provider
      value={{ user, login, googleLogin, register, onboard, logout, isAuthenticated: !!user, isLoading }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
