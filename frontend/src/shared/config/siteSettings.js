import defaultLogo from "@/assets/buddy_talk_logo.jpg";

export const SITE_SETTINGS_KEY = "buddy_talk_site_settings";

export const defaultSiteSettings = {
  brandName: "Buddy Talk",
  tagline: "AI Speaking Tutor",
  logoUrl: defaultLogo,
  contactNote: "Kênh social đang chờ cấu hình. Footer giữ sẵn vị trí để thêm link thật sau.",
  socialLinks: {
    facebook: "#",
    community: "#",
    tiktok: "#",
    email: "mailto:hello@buddytalk.local",
  },
};

export const normalizeSiteSettings = (settings = {}) => ({
  ...defaultSiteSettings,
  ...settings,
  socialLinks: {
    ...defaultSiteSettings.socialLinks,
    ...(settings.socialLinks || {}),
  },
});

export const getSiteSettings = () => {
  if (typeof window === "undefined") {
    return defaultSiteSettings;
  }

  try {
    const raw = window.localStorage.getItem(SITE_SETTINGS_KEY);
    if (!raw) {
      return defaultSiteSettings;
    }

    const parsed = JSON.parse(raw);
    return normalizeSiteSettings(parsed);
  } catch {
    return defaultSiteSettings;
  }
};

export const saveSiteSettings = (settings) => {
  const nextSettings = normalizeSiteSettings(settings);

  if (typeof window === "undefined") {
    return nextSettings;
  }

  try {
    window.localStorage.setItem(SITE_SETTINGS_KEY, JSON.stringify(nextSettings));
  } catch (error) {
    void error;
  }

  window.dispatchEvent(new CustomEvent("buddy-talk-site-settings", { detail: nextSettings }));
  return nextSettings;
};
