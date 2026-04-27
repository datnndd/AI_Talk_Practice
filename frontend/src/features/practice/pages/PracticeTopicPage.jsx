import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import TopicCard from "@/features/practice/components/TopicCard";
import { useAuth } from "@/features/auth/context/AuthContext";
import { 
  AirplaneTilt, 
  Handshake, 
  Coffee, 
  Globe, 
  Users, 
  Palette,
  Lightning,
  Question
} from "@phosphor-icons/react";
import { practiceApi } from "@/features/practice/api/practiceApi";

const CATEGORY_STYLES = {
  travel: {
    icon: AirplaneTilt,
    iconBg: "bg-primary/10",
    iconColor: "text-primary",
    badgeStyles: "bg-primary/10 text-primary border-primary/20",
    size: "md:col-span-8",
  },
  business: {
    icon: Handshake,
    iconBg: "bg-zinc-100",
    iconColor: "text-zinc-600",
    badgeStyles: "bg-amber-100 text-amber-700 border-amber-200",
    size: "md:col-span-4",
  },
  daily_life: {
    icon: Coffee,
    iconBg: "bg-emerald-50",
    iconColor: "text-emerald-600",
    badgeStyles: "bg-emerald-100 text-emerald-700 border-emerald-200",
    size: "md:col-span-4",
  },
  academic: {
    icon: Globe,
    bg: "bg-zinc-950 text-white",
    iconBg: "bg-white/10",
    iconColor: "text-white",
    badgeStyles: "bg-rose-500/20 text-rose-400 border-rose-500/30",
    size: "md:col-span-8",
  },
  social: {
    icon: Users,
    iconBg: "bg-indigo-50",
    iconColor: "text-indigo-600",
    badgeStyles: "bg-indigo-100 text-indigo-700 border-indigo-200",
    size: "md:col-span-6",
  },
  hobbies: {
    icon: Palette,
    iconBg: "bg-pink-50",
    iconColor: "text-pink-600",
    badgeStyles: "bg-pink-100 text-pink-700 border-pink-200",
    size: "md:col-span-6",
  },
};

const formatCategoryLabel = (category) =>
  category
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");

const PracticeTopic = () => {
  const { isSubscribed } = useAuth();
  const [topics, setTopics] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchScenarios = useCallback(async () => {
    try {
      const scenarios = await practiceApi.listScenarios();
      // Map API scenarios to UI format with icons and colors
      const mappedTopics = scenarios.map((scenario, index) => {
        let { icon, iconBg, iconColor, badgeStyles, size, bg } = CATEGORY_STYLES[scenario.category] || {};

        if (!icon) {
          icon = Question;
          iconBg = "bg-zinc-100";
          iconColor = "text-zinc-600";
          badgeStyles = "bg-zinc-100 text-zinc-700 border-zinc-200";
          size = "md:col-span-4";
        }

        // Just cycle through sizes if we want visual variety
        if (!size) {
           const sizes = ["md:col-span-4", "md:col-span-6", "md:col-span-8"];
           size = sizes[index % 3];
        }

        return {
          id: scenario.id,
          title: scenario.title,
          description: scenario.description,
          level: scenario.difficulty.charAt(0).toUpperCase() + scenario.difficulty.slice(1),
          duration: "10 mins",
          category: formatCategoryLabel(scenario.category),
          isLocked: Boolean(scenario.is_pro) && !isSubscribed,
          isPro: Boolean(scenario.is_pro),
          // UI properties
          icon, iconBg, iconColor, badgeStyles, size, bg,
          ...(scenario.category === "travel" && { overlay: () => <AirplaneTilt weight="fill" size={240} className="text-primary" /> }),
          ...(scenario.category === "academic" && { overlay: () => <Globe weight="fill" size={240} className="text-white" /> }),
        };
      });
      setTopics(mappedTopics);
    } catch (error) {
      console.error("Failed to fetch scenarios", error);
    } finally {
      setIsLoading(false);
    }
  }, [isSubscribed]);

  useEffect(() => {
    void fetchScenarios();
  }, [fetchScenarios]);

  return (
    <div className="mx-auto max-w-6xl">
      <header className="mb-10 flex flex-col justify-between gap-6 md:flex-row md:items-end">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Scenario Library</p>
          <h1 className="mb-2 mt-4 text-4xl font-black tracking-tight text-zinc-950 font-display">
            Choose Your Topic
          </h1>
          <p className="text-lg font-medium text-zinc-500">
            Select a scenario to start your immersive AI conversation practice.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="flex gap-2"
        >
          <Link
            to="/topics"
            className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-2.5 font-bold text-white shadow-lg shadow-primary/20 transition-all hover:scale-105 active:scale-95"
          >
            <Lightning weight="fill" />
            Quick Start
          </Link>
        </motion.div>
      </header>

      {!isSubscribed && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="mb-8 rounded-[1.75rem] border border-amber-200 bg-amber-50 px-6 py-5"
        >
          <p className="text-[11px] font-black uppercase tracking-[0.18em] text-amber-700">Free plan</p>
          <p className="mt-2 text-sm font-medium leading-7 text-amber-900">
            Free scenarios are available now. VIP scenarios are marked and require an active subscription.
          </p>
        </motion.div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 pb-12 md:grid-cols-12">
          {topics.map((topic, index) => (
            <TopicCard key={topic.id || index} card={topic} />
          ))}

          {topics.length === 0 && (
            <div className="col-span-12 py-20 text-center font-bold text-zinc-500">
              No scenarios available right now.
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PracticeTopic;
