import { useEffect, useState } from "react";
import { motion } from "framer-motion";

import { useAuth } from "@/features/auth/context/AuthContext";
import { getLeaderboardData } from "@/features/leaderboard/api/leaderboardApi";
import LeaderboardList from "@/features/leaderboard/components/LeaderboardList";
import LeaderboardPodium from "@/features/leaderboard/components/LeaderboardPodium";

const PERIOD_CONTENT = {
  weekly: {
    title: "Weekly Speaking Leaderboard",
    subtitle: "Who practiced speaking the most this week?",
  },
  all_time: {
    title: "All-time Speaking Leaderboard",
    subtitle: "The most dedicated speakers across the entire platform.",
  },
};

const LeaderboardPage = () => {
  const { user } = useAuth();
  const [period, setPeriod] = useState("weekly");
  const [data, setData] = useState({
    filters: [],
    activeFilter: "weekly",
    entries: [],
    currentUser: null,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const periodContent = PERIOD_CONTENT[data.activeFilter] ?? PERIOD_CONTENT.weekly;

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
    <div className="mx-auto max-w-5xl px-2 text-[#191c1e]">
      <main className="pb-12">
        <motion.section
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-14 text-center"
        >
          <h1 className="font-display text-4xl font-extrabold tracking-tight text-[#2b6c00] md:text-6xl">
            {periodContent.title}
          </h1>
          <p className="mt-4 text-lg font-medium text-[#3f4a36]">
            {periodContent.subtitle} <span role="img" aria-label="speaking">🗣️</span>
            <span role="img" aria-label="fire">🔥</span>
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            {data.filters.map((filter) => {
              const isActive = filter.key === data.activeFilter;

              return (
                <button
                  key={filter.key}
                  type="button"
                  onClick={() => {
                    if (filter.enabled) {
                      setPeriod(filter.key);
                    }
                  }}
                  disabled={!filter.enabled}
                  className={`rounded-full px-5 py-2.5 text-sm font-black uppercase tracking-[0.16em] transition ${
                    isActive
                      ? "bg-primary text-white shadow-lg shadow-primary/20"
                      : filter.enabled
                        ? "bg-white text-zinc-500 hover:bg-[#fbffe2] hover:text-[#2b6c00]"
                        : "cursor-not-allowed bg-white/60 text-zinc-300"
                  }`}
                  aria-pressed={isActive}
                >
                  {filter.label}
                </button>
              );
            })}
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
          <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }}>
            <LeaderboardPodium entries={data.entries} />
            <LeaderboardList entries={data.entries} currentUser={data.currentUser} />
          </motion.div>
        )}
      </main>
    </div>
  );
};

export default LeaderboardPage;
