import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Clock, ShieldStar } from "@phosphor-icons/react";

import { useAuth } from "@/features/auth/context/AuthContext";
import { getLeaderboardData } from "@/features/leaderboard/api/leaderboardApi";
import LeaderboardList from "@/features/leaderboard/components/LeaderboardList";
import "@/features/leaderboard/components/Leaderboard.css";

const LEAGUE_COLORS = [
  "#cd7f32",
  "#9ca3af",
  "#ffc800",
  "#58cc02",
  "#ff4b4b",
  "#1cb0f6",
  "#7848f4",
];

const LeagueProgression = () => {
  const activeIndex = 4;

  return (
    <div className="league-progression">
      {LEAGUE_COLORS.map((color, index) => (
        <ShieldStar
          key={index}
          size={34}
          weight="fill"
          color={color}
          className={`league-icon ${index === activeIndex ? "league-icon-active" : ""}`}
        />
      ))}
    </div>
  );
};

const LeaderboardPage = () => {
  const { user } = useAuth();
  const period = "weekly";
  const resetLabel = getWeeklyResetLabel();
  const [data, setData] = useState({
    filters: [],
    activeFilter: "weekly",
    entries: [],
    currentUser: null,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      setIsLoading(true);
      setError("");

      try {
        const nextData = await getLeaderboardData({ period, currentUserId: user?.id });
        if (isMounted) {
          setData(nextData);
        }
      } catch (requestError) {
        if (isMounted) {
          setError(requestError.response?.data?.detail || "Unable to load leaderboard right now.");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    load();

    return () => {
      isMounted = false;
    };
  }, [period, user?.id]);

  return (
    <div className="leaderboard-container">
      <main className="w-full">
        <motion.section
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center"
        >
          <LeagueProgression />
          <h1 className="league-title">Ruby League</h1>
          <p className="league-subtitle">
            Weekly XP leaderboard resets every Monday.
          </p>
          
          <div className="league-timer">
            <Clock size={20} weight="bold" />
            {resetLabel}
          </div>
        </motion.section>

        {error ? (
          <div className="mb-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-600">
            {error}
          </div>
        ) : null}

        {isLoading ? (
          <div className="flex justify-center py-24">
            <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary" />
          </div>
        ) : (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
            <LeaderboardList entries={data.entries} currentUser={data.currentUser} />
          </motion.div>
        )}
      </main>
    </div>
  );
};

const getWeeklyResetLabel = () => {
  const now = new Date();
  const nextMonday = new Date(now);
  const daysUntilMonday = (8 - now.getDay()) % 7 || 7;
  nextMonday.setDate(now.getDate() + daysUntilMonday);
  nextMonday.setHours(0, 0, 0, 0);

  const diffMs = Math.max(0, nextMonday.getTime() - now.getTime());
  const totalHours = Math.ceil(diffMs / (1000 * 60 * 60));
  const days = Math.floor(totalHours / 24);
  const hours = totalHours % 24;

  if (days <= 0) return `${hours}h until reset`;
  return `${days}d ${hours}h until reset`;
};

export default LeaderboardPage;
