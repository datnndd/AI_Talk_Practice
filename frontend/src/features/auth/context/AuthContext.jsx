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
  const [isLoading, setIsLoading] = useState(true);

  const persistTokens = useCallback(({ access_token, refresh_token }) => {
    if (access_token) localStorage.setItem("access_token", access_token);
    if (refresh_token) localStorage.setItem("refresh_token", refresh_token);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
    setGamification(null);
  }, []);

  const refreshGamification = useCallback(async () => {
    const response = await httpClient.get("/gamification/me");
    setGamification(response.data);
    return response.data;
  }, []);

  const applyGamificationReward = useCallback((reward) => {
    if (!reward) return;
    setGamification((current) => {
      if (!current) return current;
      const xpEarned = Number(reward.xp_earned || 0);
      const coinEarned = Number(reward.coin_earned || 0);
      const levelsGained = Number(reward.levels_gained || 0);
      return {
        ...current,
        xp: {
          ...current.xp,
          total: Number(current.xp?.total || 0) + xpEarned,
          today: Number(current.xp?.today || 0) + xpEarned,
          level: Number(current.xp?.level || 1) + levelsGained,
        },
        coin: {
          ...current.coin,
          balance: Number(current.coin?.balance || 0) + coinEarned,
        },
      };
    });
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
    } catch {
      logout();
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [logout, refreshGamification]);

  useEffect(() => {
    if (localStorage.getItem("access_token")) {
      void fetchUser();
    } else {
      setIsLoading(false);
    }
  }, [fetchUser]);

  const login = async (email, password) => {
    const response = await httpClient.post("/auth/login", { email, password });
    persistTokens(response.data);
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
    persistTokens(response.data);
    return response.data;
  };

  const register = async (userData) => {
    const response = await httpClient.post("/auth/register/verify", userData);
    persistTokens(response.data);
    return response.data;
  };

  const onboard = async (onboardingData) => {
    const response = await httpClient.put("/auth/me/onboard", onboardingData);
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
        updateProfileWithAvatar,
        changePassword,
        logout,
        refreshUser: fetchUser,
        gamification,
        refreshGamification,
        applyGamificationReward,
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
