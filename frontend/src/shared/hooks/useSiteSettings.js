import { useEffect, useState } from "react";

import { getSiteSettings } from "@/shared/config/siteSettings";

export const useSiteSettings = () => {
  const [settings, setSettings] = useState(getSiteSettings);

  useEffect(() => {
    const syncSettings = () => setSettings(getSiteSettings());
    const syncCustomSettings = (event) => setSettings(event.detail || getSiteSettings());

    window.addEventListener("storage", syncSettings);
    window.addEventListener("buddy-talk-site-settings", syncCustomSettings);

    return () => {
      window.removeEventListener("storage", syncSettings);
      window.removeEventListener("buddy-talk-site-settings", syncCustomSettings);
    };
  }, []);

  return settings;
};
