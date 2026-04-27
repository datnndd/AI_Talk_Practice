import { Link } from "react-router-dom";
import { Gear, PencilSimple } from "@phosphor-icons/react";

import { useAuth } from "@/features/auth/context/AuthContext";
import ProfileStats from "../components/ProfileStats";
import ProfileAchievements from "../components/ProfileAchievements";

const ProfileSettingsPage = () => {
  const { user } = useAuth();

  const displayName = user?.display_name || user?.email?.split("@")[0] || "Learner";
  const username = user?.preferences?.handle || user?.email?.split("@")[0]?.toLowerCase() || "learner";
  const joinedDate = "May 2024";

  const stats = {
    streak: user?.streak || 0,
    totalXp: user?.total_xp || 10876,
    league: user?.current_league || "Ruby",
    topFinishes: user?.top_finishes || 3,
  };

  return (
    <div className="flex flex-col gap-8 lg:flex-row">
      {/* Main Content Area */}
      <div className="flex-1 space-y-8">
        {/* Profile Header */}
        <section className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between pb-8 border-b-2 border-[#e5e5e5]">
          <div className="flex flex-col items-center gap-6 md:flex-row md:items-center">
            {/* Avatar */}
            <div className="relative group">
              <div className="h-40 w-40 overflow-hidden rounded-full border-4 border-[#e5e5e5] bg-[#4B4B4B] flex items-center justify-center">
                {user?.avatar ? (
                  <img src={user.avatar} alt={displayName} className="h-full w-full object-cover" />
                ) : (
                  <span className="text-4xl font-black text-white">{displayName.slice(0, 1).toUpperCase()}</span>
                )}
              </div>
              <Link 
                to="/settings"
                className="absolute bottom-1 right-1 h-10 w-10 rounded-full border-2 border-[#e5e5e5] bg-white flex items-center justify-center text-[#1cb0f6] shadow-sm transition-transform hover:scale-110 active:translate-y-[2px]"
              >
                <PencilSimple size={20} weight="bold" />
              </Link>
            </div>

            {/* Name/Username */}
            <div className="text-center md:text-left">
              <h1 className="text-3xl font-black text-[#4b4b4b]">{displayName}</h1>
              <p className="text-lg font-bold text-[#afafaf]">{username}</p>
              <div className="mt-2 flex flex-wrap justify-center gap-4 text-sm font-bold text-[#afafaf] md:justify-start">
                <div className="flex items-center gap-1">
                  <span>Joined {joinedDate}</span>
                </div>
                <div className="flex items-center gap-2">
                  <button className="hover:text-[#4b4b4b]">16 Following</button>
                  <button className="hover:text-[#4b4b4b]">6 Followers</button>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-center gap-3">
            <Link 
              to="/settings" // This would be the old form-based settings page
              className="flex h-12 w-12 items-center justify-center rounded-2xl border-2 border-b-4 border-[#e5e5e5] text-[#1cb0f6] transition-all hover:bg-[#f7f7f7] active:border-b-2 active:translate-y-[2px]"
            >
              <Gear size={24} weight="bold" />
            </Link>
          </div>
        </section>

        {/* Statistics Section */}
        <section>
          <h2 className="mb-4 text-2xl font-black text-[#4b4b4b]">Statistics</h2>
          <ProfileStats stats={stats} />
        </section>

        {/* Achievements Section */}
        <section>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-2xl font-black text-[#4b4b4b]">Achievements</h2>
            <Link to="/profile/achievements" className="text-sm font-black uppercase text-[#1cb0f6] hover:brightness-90">View all</Link>
          </div>
          <ProfileAchievements />
        </section>
      </div>

    </div>
  );
};

export default ProfileSettingsPage;
