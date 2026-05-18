import { useEffect, useMemo, useState } from "react";

import ScenarioPlaylistSection from "@/features/scenarios/components/ScenarioPlaylistSection";
import { useAuth } from "@/features/auth/context/AuthContext";
import { canAccessSubscriptionFeatures } from "@/features/auth/utils/subscription";
import { practiceApi } from "@/features/practice/api/practiceApi";

const ScenariosPage = () => {
  const { user } = useAuth();
  const [scenarios, setScenarios] = useState([]);
  const [isLoadingScenarios, setIsLoadingScenarios] = useState(true);
  const [scenarioError, setScenarioError] = useState("");
  const hasProAccess = useMemo(() => canAccessSubscriptionFeatures(user), [user]);

  useEffect(() => {
    let isMounted = true;

    const loadScenarios = async () => {
      const cachedScenarios = practiceApi.getCachedScenarios?.();
      const hasCachedScenarios = Boolean(cachedScenarios);

      if (cachedScenarios) {
        setScenarios(Array.isArray(cachedScenarios) ? cachedScenarios : []);
      }
      setIsLoadingScenarios(!hasCachedScenarios);
      setScenarioError("");

      try {
        const data = await practiceApi.listScenarios({ force: hasCachedScenarios });
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

    void loadScenarios();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="app-page-wide space-y-10">
      <div id="playlists">
        <ScenarioPlaylistSection scenarios={scenarios} isLoading={isLoadingScenarios} error={scenarioError} hasProAccess={hasProAccess} />
      </div>
    </div>
  );
};

export default ScenariosPage;


