import { useState } from "react";
import { Link } from "react-router-dom";
import { Gear, PencilSimple } from "@phosphor-icons/react";

import { useAuth } from "@/features/auth/context/AuthContext";
import ProfileStats from "../components/ProfileStats";
import ProfileAchievements from "../components/ProfileAchievements";

const ProfileSettingsPage = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("following");

  const displayName = user?.display_name || user?.email?.split("@")[0] || "Learner";
  const username = user?.preferences?.handle || user?.email?.split("@")[0]?.toLowerCase() || "learner";
  const joinedDate = "May 2024"; // Mock or from user data

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

      {/* Right Sidebar Area */}
      <div className="w-full space-y-8 lg:w-[350px]">
        {/* Friend Feed Mockup */}
        <div className="rounded-2xl border-2 border-[#e5e5e5] p-6">
          <div className="mb-4 flex items-center justify-between">
             <h3 className="text-xl font-black text-[#4b4b4b]">Friends</h3>
          </div>
          
          <div className="space-y-6">
             <div className="flex items-start gap-4">
                <div className="h-12 w-12 shrink-0 rounded-full bg-emerald-500 overflow-hidden">
                   <img src="https://simg-ssl.duolingo.com/ssr-avatars/323971745/SSR-XUBWDuzZa8/xlarge" alt="Friend" />
                </div>
                <div className="flex-1">
                   <div className="font-bold text-[#4b4b4b]">Nilesh K</div>
                   <div className="text-xs text-[#afafaf] mb-2">2 hours ago</div>
                   <div className="text-sm text-[#777777]">Collected the April badge!</div>
                   <button className="mt-3 flex items-center gap-2 rounded-xl border-2 border-b-4 border-[#e5e5e5] px-4 py-2 text-xs font-black text-[#1cb0f6] hover:bg-[#f7f7f7] active:border-b-2 active:translate-y-[2px]">
                      CELEBRATE
                   </button>
                </div>
             </div>
             
             <div className="flex items-start gap-4">
                <div className="h-12 w-12 shrink-0 rounded-full bg-blue-500 overflow-hidden">
                   <img src="https://simg-ssl.duolingo.com/ssr-avatars/1670885357/SSR-Y1qoFBYJ1L/xlarge" alt="Friend" />
                </div>
                <div className="flex-1">
                   <div className="font-bold text-[#4b4b4b]">samanyu ts</div>
                   <div className="text-xs text-[#afafaf] mb-2">1 day ago</div>
                   <div className="text-sm text-[#777777]">Earned 1000 XP this week!</div>
                   <button className="mt-3 flex items-center gap-2 rounded-xl border-2 border-b-4 border-[#e5e5e5] px-4 py-2 text-xs font-black text-[#1cb0f6] hover:bg-[#f7f7f7] active:border-b-2 active:translate-y-[2px]">
                      CELEBRATE
                   </button>
                </div>
             </div>
          </div>
          
          <Link to="/friends" className="mt-6 block text-center text-sm font-black uppercase text-[#1cb0f6] hover:brightness-90 border-t-2 border-[#e5e5e5] pt-4">
            View all
          </Link>
        </div>

        {/* Following/Followers Tabs */}
        <div className="rounded-2xl border-2 border-[#e5e5e5] p-6">
           <div className="flex border-b-2 border-[#e5e5e5] mb-4">
              <button 
                onClick={() => setActiveTab("following")}
                className={`flex-1 pb-2 font-black uppercase text-sm -mb-[2px] transition-colors ${activeTab === "following" ? "text-[#1cb0f6] border-b-2 border-[#1cb0f6]" : "text-[#afafaf] hover:text-[#777777]"}`}
              >
                Following
              </button>
              <button 
                onClick={() => setActiveTab("followers")}
                className={`flex-1 pb-2 font-black uppercase text-sm -mb-[2px] transition-colors ${activeTab === "followers" ? "text-[#1cb0f6] border-b-2 border-[#1cb0f6]" : "text-[#afafaf] hover:text-[#777777]"}`}
              >
                Followers
              </button>
           </div>
           
           <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
              {/* Mock users */}
              {[1, 2, 3].map(i => (
                <Link key={i} to={`/u/${i}`} className="flex items-center gap-4 group">
                  <div className="h-12 w-12 rounded-full bg-zinc-200" />
                  <div>
                    <div className="font-bold text-[#4b4b4b] group-hover:text-[#1cb0f6]">User {i}</div>
                    <div className="text-xs text-[#afafaf]">12.5k XP</div>
                  </div>
                </Link>
              ))}
           </div>
           <button className="w-full mt-4 text-center text-sm font-black uppercase text-[#1cb0f6] hover:brightness-90">View 13 more</button>
        </div>

        {/* Add Friends Section */}
        <div className="space-y-4">
           <h3 className="text-sm font-black text-[#afafaf] uppercase tracking-wide">Add friends</h3>
           <button className="flex w-full items-center gap-4 rounded-2xl border-2 border-b-4 border-[#e5e5e5] p-4 text-left hover:bg-[#f7f7f7] active:border-b-2 active:translate-y-[2px]">
              <div className="h-10 w-10 shrink-0">
                 <img src="https://d35aaqx5ub95lt.cloudfront.net/images/profile/48b8884ac9d7513e65f3a2b54984c5c4.svg" alt="Find" />
              </div>
              <span className="font-black text-[#4b4b4b] uppercase text-sm">Find friends</span>
           </button>
           <button className="flex w-full items-center gap-4 rounded-2xl border-2 border-b-4 border-[#e5e5e5] p-4 text-left hover:bg-[#f7f7f7] active:border-b-2 active:translate-y-[2px]">
              <div className="h-10 w-10 shrink-0">
                 <img src="https://d35aaqx5ub95lt.cloudfront.net/images/profile/146923c24e252de2fd1a124f57905359.svg" alt="Invite" />
              </div>
              <span className="font-black text-[#4b4b4b] uppercase text-sm">Invite friends</span>
           </button>
        </div>

        {/* Footer Links Mock */}
        <div className="flex flex-wrap gap-x-4 gap-y-2 pt-4">
           {["About", "Blog", "Store", "Efficacy", "Careers", "Investors", "Terms", "Privacy"].map(link => (
             <a key={link} href="#" className="text-xs font-black uppercase text-[#afafaf] hover:brightness-75">{link}</a>
           ))}
        </div>
      </div>
    </div>
  );
};

export default ProfileSettingsPage;
