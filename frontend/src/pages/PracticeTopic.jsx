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
  Lightning
} from "@phosphor-icons/react";

const PracticeTopic = () => {
  const topics = [
    {
      title: "Booking a Boutique Hotel",
      description: "Practice asking for specific amenities, negotiating room rates, and handling check-in details in a foreign city.",
      level: "Intermediate",
      duration: "8 mins",
      category: "Travel",
      icon: AirplaneTilt,
      size: "md:col-span-8",
      iconBg: "bg-primary/10",
      iconColor: "text-primary",
      badgeStyles: "bg-primary/10 text-primary border-primary/20",
      overlay: () => <AirplaneTilt weight="fill" size={240} className="text-primary" />
    },
    {
      title: "Negotiating a Deal",
      description: "Master the art of persuasion and professional vocabulary in a high-stakes business meeting.",
      level: "Advanced",
      duration: "10 mins",
      category: "Business",
      icon: Handshake,
      size: "md:col-span-4",
      iconBg: "bg-zinc-100",
      iconColor: "text-zinc-600",
      badgeStyles: "bg-amber-100 text-amber-700 border-amber-200"
    },
    {
      title: "Ordering at a Café",
      description: "Casual conversation practice for daily interactions and ordering your favorite drinks.",
      level: "Beginner",
      duration: "5 mins",
      category: "Daily Life",
      icon: Coffee,
      size: "md:col-span-4",
      iconBg: "bg-emerald-50",
      iconColor: "text-emerald-600",
      badgeStyles: "bg-emerald-100 text-emerald-700 border-emerald-200"
    },
    {
      title: "Climate Change & Tech",
      description: "Discussing the latest headlines and global trends. This topic updates weekly with real news snippets.",
      level: "Live Topic",
      duration: "Weekly",
      category: "Sci-Tech",
      icon: Globe,
      size: "md:col-span-8",
      bg: "bg-zinc-950 text-white",
      iconBg: "bg-white/10",
      iconColor: "text-white",
      textTitle: "text-white",
      textBody: "text-zinc-400",
      badgeStyles: "bg-rose-500/20 text-rose-400 border-rose-500/30",
      overlay: () => <Globe weight="fill" size={240} className="text-white" />
    },
    {
      title: "Board Game Night",
      description: "Learn to explain rules and make friends. Casual social vocabulary and instructions.",
      level: "Intermediate",
      duration: "7 mins",
      category: "Social",
      icon: Users,
      size: "md:col-span-6",
      iconBg: "bg-indigo-50",
      iconColor: "text-indigo-600",
      badgeStyles: "bg-indigo-100 text-indigo-700 border-indigo-200"
    },
    {
      title: "Art Gallery Visit",
      description: "Discuss artistic styles and personal feelings. Use descriptive adjectives and emotional vocabulary.",
      level: "Intermediate",
      duration: "9 mins",
      category: "Hobbies",
      icon: Palette,
      size: "md:col-span-6",
      iconBg: "bg-pink-50",
      iconColor: "text-pink-600",
      badgeStyles: "bg-pink-100 text-pink-700 border-pink-200"
    }
  ];

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

            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 pb-12">
              {topics.map((topic, index) => (
                <TopicCard key={index} card={topic} />
              ))}
            </div>
          </div>
        </main>
      </div>
      
      <MobileNav />
    </div>
  );
};

export default PracticeTopic;
