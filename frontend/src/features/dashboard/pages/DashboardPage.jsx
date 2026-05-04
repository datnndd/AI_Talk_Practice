import { useEffect, useState } from "react";

import PlaylistSection from "@/features/dashboard/components/PlaylistSection";
import { useAuth } from "@/features/auth/context/AuthContext";
import { canAccessSubscriptionFeatures } from "@/features/auth/utils/subscription";
import { practiceApi } from "@/features/practice/api/practiceApi";

const Dashboard = () => {
  const { user } = useAuth();
  const [scenarios, setScenarios] = useState([]);
  const [isLoadingScenarios, setIsLoadingScenarios] = useState(true);
  const [scenarioError, setScenarioError] = useState("");
  const hasProAccess = canAccessSubscriptionFeatures(user);

  useEffect(() => {
    let isMounted = true;

    const loadScenarios = async () => {
      const cachedScenarios = practiceApi.getCachedScenarios?.();
      if (cachedScenarios) {
        setScenarios(Array.isArray(cachedScenarios) ? cachedScenarios : []);
      }
      setIsLoadingScenarios(!cachedScenarios);
      setScenarioError("");

      try {
        const data = await practiceApi.listScenarios();
        if (isMounted) {
          setScenarios(Array.isArray(data) ? data : []);
        }
      } catch (error) {
        if (isMounted) {
          setScenarioError(error?.response?.data?.detail || "Không thể tải danh sách kịch bản.");
        }
      } finally {
        if (isMounted) {
          setIsLoadingScenarios(false);
        }
      }
    };

    const hadCachedScenarios = Boolean(practiceApi.getCachedScenarios?.());
    void loadScenarios();
    if (hadCachedScenarios) {
      void practiceApi.listScenarios({ force: true }).then((data) => {
        if (isMounted) {
          setScenarios(Array.isArray(data) ? data : []);
        }
      }).catch(() => null);
    }

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="app-page-wide space-y-10">
      <div id="playlists">
        <PlaylistSection scenarios={scenarios} isLoading={isLoadingScenarios} error={scenarioError} hasProAccess={hasProAccess} />
      </div>
    </div>
  );
};

export default Dashboard;


