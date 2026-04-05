import { motion } from "framer-motion";
import ProfileHeader from "@/features/profile/components/ProfileHeader";
import GoalProgress from "@/features/profile/components/GoalProgress";
import SubscriptionCard from "@/features/profile/components/SubscriptionCard";
import SettingsList from "@/features/profile/components/SettingsList";
import PreferencesSection from "@/features/profile/components/PreferencesSection";
import ThemeSelector from "@/features/profile/components/ThemeSelector";
import TopBar from "@/shared/components/navigation/TopBar";
import MobileNav from "@/shared/components/navigation/MobileNav";

const ProfileSettings = () => {
  return (
    <div className="min-h-[100dvh] bg-zinc-50 flex flex-col font-sans antialiased text-zinc-900">
      <TopBar />
      
      <main className="flex-1 w-full max-w-[1280px] mx-auto pt-24 px-6 pb-24 md:pb-12">
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="grid grid-cols-1 md:grid-cols-12 gap-8"
        >
          <ProfileHeader />
          <GoalProgress />
          <SubscriptionCard />
          <SettingsList />
          <PreferencesSection />
          <ThemeSelector />
        </motion.div>

        <footer className="mt-16 flex flex-col md:flex-row items-center justify-between py-10 border-t border-zinc-200">
          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.2em]">© 2024 LingoAI. High-intensity Language Practice.</p>
          <div className="flex gap-8 mt-6 md:mt-0">
            {["Help Center", "Terms", "Privacy"].map((item) => (
              <a key={item} className="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.2em] hover:text-primary transition-colors" href="#">
                {item}
              </a>
            ))}
          </div>
        </footer>
      </main>

      <MobileNav />
    </div>
  );
};

export default ProfileSettings;
