import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import MobileNav from "../components/MobileNav";
import TopicCard from "../components/TopicCard";
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
import { api } from "../contexts/AuthContext";

const PracticeTopic = () => {
  const [topics, setTopics] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchScenarios();
  }, []);

  const fetchScenarios = async () => {
    try {
      const response = await api.get("/scenarios");
      // Map API scenarios to UI format with icons and colors
      const mappedTopics = response.data.map((scenario, index) => {
        let icon, iconBg, iconColor, badgeStyles, size, bg;
        
        switch (scenario.category) {
          case "Travel":
            icon = AirplaneTilt; iconBg = "bg-primary/10"; iconColor = "text-primary"; badgeStyles = "bg-primary/10 text-primary border-primary/20"; size = "md:col-span-8";
            break;
          case "Business":
            icon = Handshake; iconBg = "bg-zinc-100"; iconColor = "text-zinc-600"; badgeStyles = "bg-amber-100 text-amber-700 border-amber-200"; size = "md:col-span-4";
            break;
          case "Daily Life":
            icon = Coffee; iconBg = "bg-emerald-50"; iconColor = "text-emerald-600"; badgeStyles = "bg-emerald-100 text-emerald-700 border-emerald-200"; size = "md:col-span-4";
            break;
          case "Sci-Tech":
            icon = Globe; bg = "bg-zinc-950 text-white"; iconBg = "bg-white/10"; iconColor = "text-white"; badgeStyles = "bg-rose-500/20 text-rose-400 border-rose-500/30"; size = "md:col-span-8";
            break;
          case "Social":
            icon = Users; iconBg = "bg-indigo-50"; iconColor = "text-indigo-600"; badgeStyles = "bg-indigo-100 text-indigo-700 border-indigo-200"; size = "md:col-span-6";
            break;
          case "Hobbies":
            icon = Palette; iconBg = "bg-pink-50"; iconColor = "text-pink-600"; badgeStyles = "bg-pink-100 text-pink-700 border-pink-200"; size = "md:col-span-6";
            break;
          default:
            icon = Question; iconBg = "bg-purple-50"; iconColor = "text-purple-600"; badgeStyles = "bg-purple-100 text-purple-700 border-purple-200"; size = "md:col-span-4";
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
          category: scenario.category,
          // UI properties
          icon, iconBg, iconColor, badgeStyles, size, bg,
          ...(scenario.category === "Travel" && { overlay: () => <AirplaneTilt weight="fill" size={240} className="text-primary" /> }),
          ...(scenario.category === "Sci-Tech" && { overlay: () => <Globe weight="fill" size={240} className="text-white" /> }),
        };
      });
      setTopics(mappedTopics);
    } catch (error) {
      console.error("Failed to fetch scenarios", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[100dvh] bg-zinc-50 flex flex-col">
      <TopBar />
      
      <div className="flex flex-1 pt-16">
        <Sidebar />
        
        <main className="flex-1 lg:ml-64 p-6 md:p-10 mb-24 lg:mb-0 overflow-y-auto">
          <div className="max-w-6xl mx-auto">
            <header className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5 }}
              >
                <h1 className="text-4xl font-black tracking-tight text-zinc-950 mb-2 font-display">
                  Choose Your Topic
                </h1>
                <p className="text-zinc-500 text-lg font-medium">
                  Select a scenario to start your immersive AI conversation practice.
                </p>
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="flex gap-2"
              >
                <button className="bg-primary text-white px-6 py-2.5 rounded-full font-bold shadow-lg shadow-primary/20 hover:scale-105 active:scale-95 transition-all inline-flex items-center gap-2">
                  <Lightning weight="fill" />
                  Quick Start
                </button>
              </motion.div>
            </header>

            {isLoading ? (
              <div className="flex justify-center items-center py-20">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6 pb-12">
                {topics.map((topic, index) => (
                  <TopicCard key={topic.id || index} card={topic} />
                ))}
                
                {topics.length === 0 && (
                  <div className="col-span-12 text-center py-20 text-zinc-500 font-bold">
                    No scenarios available right now.
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
      
      <MobileNav />
    </div>
  );
};

export default PracticeTopic;
