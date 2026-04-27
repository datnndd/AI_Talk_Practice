import { httpClient } from "@/shared/api/httpClient";

const COUNTRY_BY_LANGUAGE = {
  en: "🇺🇸",
  de: "🇩🇪",
  es: "🇪🇸",
  fr: "🇫🇷",
  vi: "🇻🇳",
  zh: "🇨🇳",
  ja: "🇯🇵",
};

const getDisplayName = (entry) => entry.display_name || entry.email?.split("@")[0] || "Learner";

const normalizeEntry = (entry, currentUserId, topScore) => ({
  id: `leaderboard-${entry.user_id}`,
  userId: entry.user_id,
  rank: entry.rank,
  name: getDisplayName(entry),
  xp: entry.score,
  country: COUNTRY_BY_LANGUAGE[entry.target_language] ?? "🌍",
  avatar: entry.avatar ?? "",
  progress: topScore > 0 ? Math.max(12, Math.round((entry.score / topScore) * 100)) : 0,
  encouragement: entry.user_id === currentUserId ? "Keep going!" : "",
  accent:
    entry.rank === 1
      ? "gold"
      : entry.rank === 2
        ? "silver"
        : entry.rank === 3
          ? "bronze"
          : entry.user_id === currentUserId
            ? "current"
            : "list",
});

export const getLeaderboardData = async ({ period = "weekly", currentUserId }) => {
  const { data } = await httpClient.get("/gamification/leaderboard", {
    params: { period },
  });
  const topScore = data.entries[0]?.score ?? data.current_user?.score ?? 0;

  return {
    filters: [
      { key: "weekly", label: "Weekly", enabled: true },
      { key: "all_time", label: "All-time", enabled: true },
      { key: "friends", label: "Friends", enabled: false },
      { key: "global", label: "Global", enabled: false },
    ],
    activeFilter: data.period,
    entries: data.entries.map((entry) => normalizeEntry(entry, currentUserId, topScore)),
    currentUser: normalizeEntry(data.current_user, currentUserId, topScore),
  };
};
