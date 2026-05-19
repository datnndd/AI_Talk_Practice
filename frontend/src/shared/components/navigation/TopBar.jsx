import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Crown, Fire, Moon, Sun } from "@phosphor-icons/react";
import { useAuth } from "@/features/auth/context/AuthContext";
import { canAccessSubscriptionFeatures } from "@/features/auth/utils/subscription";
import { getApiErrorMessage, httpClient } from "@/shared/api/httpClient";
import { useTheme } from "@/shared/context/ThemeContext";

const weekDays = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];

const formatCalendarMonth = (calendarMonth, fallbackDate = new Date()) => {
  if (!calendarMonth) return `Tháng ${fallbackDate.getMonth() + 1}/${fallbackDate.getFullYear()}`;
  const [year, month] = calendarMonth.split("-");
  return `Tháng ${Number(month)}/${year}`;
};

const toLocalDateKey = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const buildFallbackCalendarDays = (referenceDate = new Date()) => {
  const year = referenceDate.getFullYear();
  const month = referenceDate.getMonth();
  const todayKey = toLocalDateKey(new Date());
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  return Array.from({ length: daysInMonth }, (_, index) => {
    const date = new Date(year, month, index + 1);
    const dateKey = toLocalDateKey(date);
    return {
      date: dateKey,
      day: index + 1,
      checked_in: false,
      streak_day: null,
      coin_earned: 0,
      is_today: dateKey === todayKey,
    };
  });
};

const getCalendarOffset = (calendarDays) => {
  if (!calendarDays?.length) return 0;
  const firstDate = new Date(`${calendarDays[0].date}T00:00:00`);
  return (firstDate.getDay() + 6) % 7;
};

const formatNotificationTime = (value) => {
  if (!value) return "";

  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
};

const TopBar = () => {
  const { user, gamification, checkInDaily, refreshGamification } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [isStreakOpen, setIsStreakOpen] = useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [isNotificationLoading, setIsNotificationLoading] = useState(false);
  const [notificationError, setNotificationError] = useState("");
  const [isCheckingIn, setIsCheckingIn] = useState(false);
  const [checkInError, setCheckInError] = useState("");
  const streakRef = useRef(null);
  const notificationRef = useRef(null);
  const isDark = theme === "dark";

  const level = gamification?.xp?.level || 1;
  const coins = gamification?.coin?.balance || 0;
  const checkIn = gamification?.check_in;
  const streak = checkIn?.current_streak || 0;
  const calendarDays = checkIn?.calendar_days?.length ? checkIn.calendar_days : buildFallbackCalendarDays();
  const calendarOffset = getCalendarOffset(calendarDays);
  const checkedInCount = calendarDays.filter((day) => day.checked_in).length;
  const checkInStatus = checkIn?.checked_in_today
    ? "Đã check-in hôm nay"
    : `Nhận +${checkIn?.today_coin_reward || 0} Coin hôm nay`;
  const checkInHint = checkIn?.checked_in_today
    ? "Bạn đã giữ streak hôm nay."
    : "Đăng nhập mỗi ngày để giữ streak.";
  const initials = user?.display_name?.charAt(0).toUpperCase() || user?.email?.charAt(0).toUpperCase() || "D";
  const hasProAccess = canAccessSubscriptionFeatures(user);
  const unreadNotificationCount = notifications.filter((notification) => !notification.read_at).length;

  useEffect(() => {
    if (!isStreakOpen && !isNotificationOpen) return undefined;

    const handlePointerDown = (event) => {
      if (isStreakOpen && !streakRef.current?.contains(event.target)) {
        setIsStreakOpen(false);
      }
      if (isNotificationOpen && !notificationRef.current?.contains(event.target)) {
        setIsNotificationOpen(false);
      }
    };
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        setIsStreakOpen(false);
        setIsNotificationOpen(false);
      }
    };

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isNotificationOpen, isStreakOpen]);

  useEffect(() => {
    if (!isNotificationOpen) return undefined;

    let isMounted = true;
    setIsNotificationLoading(true);
    setNotificationError("");
    httpClient
      .get("/notifications", { params: { page_size: 10 } })
      .then(({ data }) => {
        if (isMounted) {
          setNotifications(data?.items || []);
        }
      })
      .catch((error) => {
        if (isMounted) {
          setNotificationError(getApiErrorMessage(error, "Không thể tải thông báo."));
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsNotificationLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [isNotificationOpen]);

  const handleCheckIn = async () => {
    if (checkIn?.checked_in_today || isCheckingIn) return;
    setIsCheckingIn(true);
    setCheckInError("");
    try {
      await checkInDaily();
    } catch (error) {
      setCheckInError(error?.response?.data?.detail || "Không thể điểm danh. Vui lòng thử lại.");
      await refreshGamification?.().catch(() => null);
    } finally {
      setIsCheckingIn(false);
    }
  };

  const handleToggleNotifications = () => {
    setIsNotificationOpen((current) => !current);
  };

  const handleReadNotification = async (notificationId) => {
    setNotifications((current) =>
      current.map((notification) =>
        notification.id === notificationId
          ? { ...notification, read_at: notification.read_at || new Date().toISOString() }
          : notification,
      ),
    );

    try {
      const { data } = await httpClient.post(`/notifications/${notificationId}/read`);
      setNotifications((current) =>
        current.map((notification) => (notification.id === notificationId ? data : notification)),
      );
    } catch (error) {
      setNotificationError(getApiErrorMessage(error, "Không thể đánh dấu đã đọc."));
    }
  };

  return (
    <div className="flex items-center gap-6 px-8 py-4 bg-background border-b border-border sticky top-0 z-40">
      <div className="ml-auto flex items-center gap-1 rounded-full border border-border bg-card px-2 py-1.5 shadow-sm">
        <div className="flex items-center gap-2 px-3 py-1">
          <span className="text-lg leading-none">⭐</span>
          <div className="leading-tight">
            <p className="text-sm font-extrabold text-foreground">{level}</p>
            <p className="-mt-0.5 text-[9px] font-bold uppercase tracking-wide text-muted-foreground">Cấp độ</p>
          </div>
        </div>
        <span className="h-6 w-px bg-border" />
        <div ref={streakRef} className="relative flex items-center gap-2 px-3 py-1" onMouseEnter={() => setIsStreakOpen(true)}>
          <button
            type="button"
            aria-expanded={isStreakOpen}
            aria-label="M? l?ch streak"
            onClick={() => setIsStreakOpen((value) => !value)}
            className="flex items-center gap-2 rounded-2xl outline-none transition hover:opacity-90 focus-visible:ring-2 focus-visible:ring-[#ff9600]/60"
          >
            <Fire size={18} weight="fill" className="text-[#ff9600]" />
            <div className="leading-tight text-left">
              <p className="text-sm font-extrabold text-[#ff9600]">{streak}</p>
              <p className="-mt-0.5 text-[9px] font-bold uppercase tracking-wide text-muted-foreground">Streak</p>
            </div>
          </button>
          <div className={`absolute left-1/2 top-full z-50 mt-3 w-[360px] -translate-x-1/2 transition duration-150 ${isStreakOpen ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"}`}>
            <div className="relative overflow-hidden rounded-[1.75rem] border border-orange-200/80 bg-gradient-to-br from-white via-orange-50 to-amber-50 p-4 text-zinc-900 shadow-[0_24px_70px_-32px_rgba(255,150,0,0.75)] dark:border-orange-400/20 dark:from-zinc-950 dark:via-zinc-900 dark:to-orange-950/40 dark:text-zinc-50">
              <div className="absolute -top-2 left-1/2 h-4 w-4 -translate-x-1/2 rotate-45 border-l border-t border-orange-200/80 bg-white dark:border-orange-400/20 dark:bg-zinc-950" />
              <div className="pointer-events-none absolute -right-10 -top-10 h-28 w-28 rounded-full bg-orange-300/25 blur-2xl" />
              <div className="pointer-events-none absolute -bottom-16 -left-12 h-32 w-32 rounded-full bg-amber-200/35 blur-3xl" />

              <div className="relative flex items-center gap-3">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-400 to-amber-500 text-white shadow-[0_14px_30px_-16px_rgba(255,150,0,0.9)]">
                  <Fire size={32} weight="fill" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-orange-500/80">Daily streak</p>
                  <div className="mt-1 flex items-end gap-2">
                    <p className="text-3xl font-black leading-none text-[#ff9600]">{streak}</p>
                    <p className="pb-0.5 text-sm font-extrabold text-zinc-500 dark:text-zinc-300">ngày liên tiếp</p>
                  </div>
                </div>
                <div className="rounded-2xl border border-orange-200 bg-white/80 px-3 py-2 text-right shadow-sm dark:border-orange-400/20 dark:bg-white/10">
                  <p className="text-[10px] font-black uppercase text-zinc-400">Tháng này</p>
                  <p className="text-sm font-black text-[#ff9600]">{checkedInCount}/{calendarDays.length}</p>
                </div>
              </div>

              <div className="relative mt-4 rounded-2xl border border-orange-100 bg-white/75 p-3 shadow-inner dark:border-white/10 dark:bg-white/5">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-black text-zinc-900 dark:text-white">{formatCalendarMonth(checkIn?.calendar_month)}</p>
                    <p className="mt-0.5 text-[11px] font-bold text-zinc-500 dark:text-zinc-400">{checkInStatus}</p>
                  </div>
                  <span className="rounded-full bg-orange-100 px-3 py-1 text-[10px] font-black uppercase tracking-wide text-[#ff9600] dark:bg-orange-400/10">
                    Lịch check-in
                  </span>
                </div>

                <div className="rounded-xl bg-orange-50/80 p-2 dark:bg-black/20">
                  <div className="grid grid-cols-7 gap-1 text-center text-[10px] font-black text-orange-400/80">
                    {weekDays.map((day) => (
                      <span key={day} className="py-1">{day}</span>
                    ))}
                  </div>
                  <div className="mt-1 grid grid-cols-7 gap-1.5">
                    {Array.from({ length: calendarOffset }).map((_, index) => (
                      <span key={`blank-${index}`} className="aspect-square" />
                    ))}
                    {calendarDays.map((day) => (
                      <span
                        key={day.date}
                        title={day.checked_in ? `${day.date}: streak ${day.streak_day}, +${day.coin_earned} Coin` : day.date}
                        className={`relative flex aspect-square items-center justify-center rounded-xl text-xs font-black transition ${
                          day.checked_in
                            ? "bg-gradient-to-br from-[#ff9600] to-[#ffbf2f] text-white shadow-[0_8px_16px_-10px_rgba(255,150,0,0.95)]"
                            : day.is_today
                              ? "border-2 border-[#ff9600] bg-orange-100 text-[#ff9600] dark:bg-orange-400/10"
                              : "bg-white text-zinc-400 shadow-sm dark:bg-white/5 dark:text-zinc-500"
                        }`}
                      >
                        {day.day}
                        {day.checked_in ? (
                          <span className="absolute -right-0.5 -top-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-white text-[9px] font-black text-[#ff9600] shadow-sm">
                            ✓
                          </span>
                        ) : null}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <button
                type="button"
                disabled={checkIn?.checked_in_today || isCheckingIn}
                onClick={handleCheckIn}
                className={`relative mt-3 w-full rounded-2xl px-4 py-2 text-center text-xs font-extrabold transition ${
                  checkIn?.checked_in_today
                    ? "cursor-default bg-[#ff9600]/10 text-[#ff9600]"
                    : "bg-[#ff9600] text-white shadow-[0_12px_24px_-16px_rgba(255,150,0,0.95)] hover:bg-[#ff8a00] disabled:cursor-wait disabled:opacity-70"
                }`}
              >
                {checkIn?.checked_in_today ? checkInHint : isCheckingIn ? "Đang điểm danh..." : `Điểm danh nhận +${checkIn?.today_coin_reward || 0} Coin`}
              </button>
              {checkInError ? (
                <p className="relative mt-2 text-center text-[11px] font-bold text-rose-500">{checkInError}</p>
              ) : null}
            </div>
          </div>
        </div>
        <span className="h-6 w-px bg-border" />
        <div className="flex items-center gap-2 px-3 py-1">
          <span className="text-base leading-none">🪙</span>
          <div className="leading-tight">
            <p className="text-sm font-extrabold text-brand-blue">{coins.toLocaleString("en-US")}</p>
            <p className="-mt-0.5 text-[9px] font-bold uppercase tracking-wide text-muted-foreground">Coin</p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={toggleTheme}
          aria-label="Chuyển chế độ sáng/tối"
          className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-card hover:bg-muted transition-colors text-foreground/70"
        >
          {isDark ? <Sun size={20} weight="bold" /> : <Moon size={20} weight="bold" />}
        </button>

        <div ref={notificationRef} className="relative">
          <button
            type="button"
            onClick={handleToggleNotifications}
            aria-label="Thông báo"
            aria-expanded={isNotificationOpen}
            className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-card hover:bg-muted transition-colors relative"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-bell h-5 w-5 text-foreground/70" aria-hidden="true">
              <path d="M10.268 21a2 2 0 0 0 3.464 0"></path>
              <path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326"></path>
            </svg>
            {unreadNotificationCount > 0 ? (
              <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full border-2 border-card bg-brand-red px-1 text-[10px] font-black text-white">
                {unreadNotificationCount > 9 ? "9+" : unreadNotificationCount}
              </span>
            ) : null}
          </button>

          {isNotificationOpen ? (
            <div className="absolute right-0 top-12 z-50 w-[min(22rem,calc(100vw-2rem))] overflow-hidden rounded-3xl border border-border bg-card shadow-2xl shadow-zinc-950/10">
              <div className="flex items-center justify-between border-b border-border px-5 py-4">
                <div>
                  <p className="text-sm font-black text-foreground">Thông báo</p>
                  <p className="mt-0.5 text-xs font-semibold text-muted-foreground">
                    {unreadNotificationCount > 0 ? `${unreadNotificationCount} chưa đọc` : "Không có thông báo mới"}
                  </p>
                </div>
              </div>

              <div className="max-h-96 overflow-y-auto p-2">
                {isNotificationLoading ? (
                  <div className="p-5 text-center text-sm font-bold text-muted-foreground">Đang tải thông báo...</div>
                ) : notificationError ? (
                  <div className="p-5 text-center text-sm font-bold text-rose-500">{notificationError}</div>
                ) : notifications.length ? (
                  notifications.map((notification) => (
                    <button
                      type="button"
                      key={notification.id}
                      onClick={() => handleReadNotification(notification.id)}
                      className={`w-full rounded-2xl p-4 text-left transition hover:bg-muted ${
                        notification.read_at ? "opacity-70" : "bg-primary/5"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${notification.read_at ? "bg-border" : "bg-brand-red"}`} />
                        <span className="min-w-0">
                          <span className="block text-sm font-black text-foreground">{notification.title}</span>
                          <span className="mt-1 block text-sm font-medium leading-6 text-muted-foreground">{notification.body}</span>
                          <span className="mt-2 block text-[11px] font-bold text-muted-foreground">{formatNotificationTime(notification.created_at)}</span>
                        </span>
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="p-5 text-center text-sm font-bold text-muted-foreground">Bạn chưa có thông báo.</div>
                )}
              </div>
            </div>
          ) : null}
        </div>

        <Link
          to="/profile"
          className={`relative flex h-11 w-11 items-center justify-center rounded-full text-sm font-bold transition-opacity hover:opacity-90 ${
            hasProAccess
              ? "bg-gradient-to-br from-amber-200 to-yellow-500 p-[3px] shadow-[0_0_18px_rgba(251,191,36,0.75)]"
              : "bg-gradient-to-br from-zinc-200 to-zinc-500 p-[2px] shadow-[0_0_8px_rgba(113,113,122,0.25)]"
          }`}
        >
          <span className="flex h-full w-full items-center justify-center overflow-hidden rounded-full bg-foreground text-background">
            {user?.avatar ? <img src={user.avatar} alt="Profile" className="h-full w-full object-cover" /> : initials}
          </span>
          <span className={`absolute -right-1 -top-1 flex h-5 w-5 rotate-12 items-center justify-center rounded-full border ${
            hasProAccess
              ? "border-amber-200 bg-amber-300 text-amber-900 shadow-[0_0_10px_rgba(251,191,36,0.9)]"
              : "border-zinc-300 bg-zinc-200 text-zinc-500"
          }`}>
            <Crown size={12} weight="fill" />
          </span>
        </Link>
      </div>
    </div>
  );
};

export default TopBar;
