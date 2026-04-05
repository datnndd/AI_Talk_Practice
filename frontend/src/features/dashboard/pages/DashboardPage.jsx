import { motion } from "framer-motion";
import TopBar from "@/shared/components/navigation/TopBar";
import Sidebar from "@/shared/components/navigation/Sidebar";
import MobileNav from "@/shared/components/navigation/MobileNav";
import ProgressCircle from "@/features/dashboard/components/ProgressCircle";
import StreakCard from "@/features/dashboard/components/StreakCard";
import LessonStack from "@/features/dashboard/components/LessonStack";
import QuickPracticeCard from "@/features/dashboard/components/QuickPracticeCard";
import { useAuth } from "@/features/auth/context/AuthContext";

const Dashboard = () => {
  const { user, isSubscribed, subscriptionTier } = useAuth();
  const displayName = user?.display_name || user?.email?.split("@")[0] || "Learner";

  return (
    <div className="min-h-[100dvh] bg-zinc-50 flex font-sans antialiased text-zinc-900 overflow-hidden">
      <Sidebar />
      
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        <TopBar />
        
        <main className="flex-1 overflow-y-auto p-6 md:p-10 pb-32 lg:pb-10 custom-scrollbar">
          <div className="max-w-7xl mx-auto">
            <header className="flex justify-between items-end mb-12 px-2">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <h1 className="text-4xl md:text-5xl font-black tracking-tight text-zinc-950 font-display">
                  Good afternoon, <span className="text-primary italic">{displayName}</span>
                </h1>
                <p className="text-zinc-500 mt-3 font-bold uppercase tracking-widest text-xs">
                  {isSubscribed
                    ? `Subscriber mode enabled. ${subscriptionTier} practice is unlocked.`
                    : "Free mode enabled. Browse topics and upgrade to start live AI practice."}
                </p>
              </motion.div>
              
              <div className="hidden md:flex -space-x-3 items-center">
                {[1, 2, 3].map((i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, scale: 0.5 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.1 }}
                    className="w-11 h-11 rounded-full border-4 border-white shadow-sm overflow-hidden"
                  >
                    <img src={`https://i.pravatar.cc/150?u=${i}`} alt="Buddy" className="w-full h-full object-cover" />
                  </motion.div>
                ))}
                <div className="w-11 h-11 rounded-full border-4 border-white bg-zinc-100 flex items-center justify-center text-[10px] font-black text-zinc-400 shadow-sm z-10 transition-transform hover:scale-110 cursor-pointer">+2</div>
              </div>
            </header>

            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="grid grid-cols-1 md:grid-cols-12 gap-6 auto-rows-[160px]"
            >
              <ProgressCircle />
              <StreakCard />
              <QuickPracticeCard />
              <LessonStack />
            </motion.div>
          </div>
        </main>
      </div>

      <MobileNav />
    </div>
  );
};

export default Dashboard;
