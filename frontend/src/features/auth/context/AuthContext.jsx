import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { httpClient } from "@/shared/api/httpClient";
import {
  canAccessSubscriptionFeatures,
  getUserAccessLevel,
  normalizeSubscription,
} from "@/features/auth/utils/subscription";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [gamification, setGamification] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("access_token"));
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setToken(null);
    setUser(null);
    setGamification(null);
  }, []);

  const refreshGamification = useCallback(async () => {
    const response = await httpClient.get("/gamification/me");
    setGamification(response.data);
    return response.data;
  }, []);

  const checkInDaily = useCallback(async () => {
    const response = await httpClient.post("/gamification/check-in");
    setGamification(response.data.dashboard);
    return response.data;
  }, []);

  const fetchUser = useCallback(async () => {
    try {
      const response = await httpClient.get("/auth/me");
      setUser(response.data);
      void refreshGamification().catch(() => null);
      return response.data;
    } catch (error) {
      console.error("Failed to fetch user", error);
      logout();
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [logout, refreshGamification]);

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

  const checkIdentity = async (email) => {
    const response = await httpClient.post("/auth/identity", { email });
    return response.data;
  };

  const requestOtp = async ({ email, purpose }) => {
    const response = await httpClient.post("/auth/otp/request", { email, purpose });
    return response.data;
  };

  const verifyOtp = async ({ email, purpose, otp }) => {
    const response = await httpClient.post("/auth/otp/verify", { email, purpose, otp });
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
    const response = await httpClient.post("/auth/register/verify", userData);
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

  const updateProfile = async (profileData) => {
    const response = await httpClient.patch("/users/me", profileData);
    setUser(response.data);
    return response.data;
  };

  const updateProfileWithAvatar = async (profileData, avatarFile) => {
    const formData = new FormData();
    Object.entries(profileData).forEach(([key, value]) => {
      if (value !== undefined && value !== null) formData.append(key, value);
    });
    if (avatarFile) formData.append("file", avatarFile);
    const response = await httpClient.patch("/users/me/with-avatar", formData);
    setUser(response.data);
    return response.data;
  };

  const uploadAvatar = async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await httpClient.post("/users/me/avatar", formData);
    setUser(response.data);
    return response.data;
  };

  const changePassword = async (passwordData) => {
    const response = await httpClient.post("/users/me/change-password", passwordData);
    return response.data;
  };

  const forgotPassword = async (email) => {
    const response = await httpClient.post("/auth/forgot-password", { email });
    return response.data;
  };

  const resetPassword = async (data) => {
    const response = await httpClient.post("/auth/reset-password", data);
    return response.data;
  };

  const subscription = normalizeSubscription(user?.subscription);
  const isSubscribed = canAccessSubscriptionFeatures(user);
  const accessLevel = getUserAccessLevel(user);
  const hasFeature = (featureKey) =>
    Boolean(user?.is_admin) || Boolean(subscription.features?.[featureKey]) || isSubscribed;

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        checkIdentity,
        requestOtp,
        verifyOtp,
        googleLogin,
        register,
        forgotPassword,
        resetPassword,
        onboard,
        updateProfile,
        updateProfileWithAvatar,
        uploadAvatar,
        changePassword,
        logout,
        refreshUser: fetchUser,
        gamification,
        refreshGamification,
        checkInDaily,
        isAuthenticated: !!user,
        isLoading,
        subscription,
        subscriptionTier: subscription.tier,
        hasActiveSubscription: subscription.isActive,
        isSubscribed,
        accessLevel,
        hasFeature,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
