import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Gear, PencilSimple } from "@phosphor-icons/react";

import { useAuth } from "@/features/auth/context/AuthContext";
import { gamificationApi } from "@/features/gamification/api/gamificationApi";
import ProfileStats from "../components/ProfileStats";

const formatDate = (value) => {
  if (!value) return "Chưa rõ";
  try {
    return new Intl.DateTimeFormat("vi-VN", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    }).format(new Date(value));
  } catch {
    return "Chưa rõ";
  }
};

const asList = (value) => {
  if (!value) return [];
  if (Array.isArray(value)) return value.filter(Boolean);
  if (typeof value === "string") {
    return value.split(",").map((item) => item.trim()).filter(Boolean);
  }
  return [];
};

const emptyText = "Chưa cập nhật";

const ProfileSettingsPage = () => {
  const { user } = useAuth();
  const [gamification, setGamification] = useState(null);

  useEffect(() => {
    gamificationApi.getDashboard().then(setGamification).catch(() => {});
  }, []);

  const displayName = user?.display_name || user?.email?.split("@")[0] || "Learner";
  const username = user?.preferences?.handle || user?.email?.split("@")[0]?.toLowerCase() || "learner";
  const topics = asList(user?.favorite_topics);

  const stats = {
    level: gamification?.xp?.level || 1,
    totalXp: gamification?.xp?.total || 0,
    coin: gamification?.coin?.balance || 0,
    checkInStreak: gamification?.check_in?.current_streak || 0,
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
              <p className="text-lg font-bold text-[#afafaf]">@{username}</p>
              <div className="mt-2 flex flex-wrap justify-center gap-4 text-sm font-bold text-[#afafaf] md:justify-start">
                <div className="flex items-center gap-1">
                  <span>Tham gia {formatDate(user?.created_at)}</span>
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

        <section className="space-y-4">
          <h2 className="text-2xl font-black text-[#4b4b4b]">Thông tin học viên</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border-2 border-[#e5e5e5] bg-white p-4">
              <p className="text-xs font-black uppercase tracking-wide text-[#afafaf]">Email</p>
              <p className="mt-1 font-bold text-[#4b4b4b]">{user?.email || emptyText}</p>
            </div>
            <div className="rounded-2xl border-2 border-[#e5e5e5] bg-white p-4">
              <p className="text-xs font-black uppercase tracking-wide text-[#afafaf]">Trình độ</p>
              <p className="mt-1 font-bold text-[#4b4b4b]">{user?.level || emptyText}</p>
            </div>
            <div className="rounded-2xl border-2 border-[#e5e5e5] bg-white p-4">
              <p className="text-xs font-black uppercase tracking-wide text-[#afafaf]">Ngôn ngữ</p>
              <p className="mt-1 font-bold text-[#4b4b4b]">
                {user?.native_language || "vi"} → {user?.target_language || "en"}
              </p>
            </div>
            <div className="rounded-2xl border-2 border-[#e5e5e5] bg-white p-4">
              <p className="text-xs font-black uppercase tracking-wide text-[#afafaf]">Mục tiêu mỗi ngày</p>
              <p className="mt-1 font-bold text-[#4b4b4b]">
                {user?.daily_goal ? `${user.daily_goal} phút` : emptyText}
              </p>
            </div>
            <div className="rounded-2xl border-2 border-[#e5e5e5] bg-white p-4">
              <p className="text-xs font-black uppercase tracking-wide text-[#afafaf]">Mục tiêu học</p>
              <p className="mt-1 font-bold text-[#4b4b4b]">{user?.learning_purpose || emptyText}</p>
            </div>
            <div className="rounded-2xl border-2 border-[#e5e5e5] bg-white p-4">
              <p className="text-xs font-black uppercase tracking-wide text-[#afafaf]">Thử thách chính</p>
              <p className="mt-1 font-bold text-[#4b4b4b]">{user?.main_challenge || emptyText}</p>
            </div>
          </div>

          <div className="rounded-2xl border-2 border-[#e5e5e5] bg-white p-4">
            <p className="text-xs font-black uppercase tracking-wide text-[#afafaf]">Chủ đề yêu thích</p>
            {topics.length > 0 ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {topics.map((topic) => (
                  <span key={topic} className="rounded-full bg-[#ddf4ff] px-3 py-1 text-sm font-black text-[#1cb0f6]">
                    {topic}
                  </span>
                ))}
              </div>
            ) : (
              <p className="mt-1 font-bold text-[#4b4b4b]">{emptyText}</p>
            )}
          </div>
        </section>
      </div>

    </div>
  );
};

export default ProfileSettingsPage;
