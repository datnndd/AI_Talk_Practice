import axios from "axios";
import { createContext, useContext, useState, useEffect } from "react";

const ApiContext = createContext();

export const api = axios.create({
  baseURL: "http://localhost:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("access_token"));
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetchUser();
    } else {
      setIsLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await api.get("/auth/me");
      setUser(response.data);
    } catch (error) {
      console.error("Failed to fetch user", error);
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await api.post("/auth/login", { email, password });
    const { access_token } = response.data;
    localStorage.setItem("access_token", access_token);
    setToken(access_token);
    
    // Fetch user immediately to know onboarding status
    const userRes = await api.get("/auth/me", { 
      headers: { Authorization: `Bearer ${access_token}` } 
    });
    setUser(userRes.data);
    return userRes.data;
  };

  const register = async (userData) => {
    const response = await api.post("/auth/register", userData);
    const { access_token } = response.data;
    localStorage.setItem("access_token", access_token);
    setToken(access_token);
    return access_token;
  };

  const onboard = async (onboardingData) => {
    const response = await api.put("/auth/me/onboard", onboardingData);
    setUser(response.data);
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{ user, login, register, onboard, logout, isAuthenticated: !!user, isLoading }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
