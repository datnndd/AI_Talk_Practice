import { Crown, Medal } from "@phosphor-icons/react";

const accentStyles = {
  gold: {
    card: "bg-gradient-to-b from-[#ffb34c] to-[#ffe4bf] border-b-[8px] border-[#8c5000] shadow-[0px_20px_60px_rgba(255,215,9,0.28)]",
    badge: "bg-[#8c5000] text-white border-[#ffca86]",
    medal: "text-[#ffcf86]",
    bar: "bg-[#8c5000]",
  },
  silver: {
    card: "bg-white border-b-[8px] border-slate-300 shadow-[0px_10px_40px_rgba(49,60,15,0.04)]",
    badge: "bg-slate-300 text-white border-white",
    medal: "text-slate-400",
    bar: "bg-slate-400",
  },
  bronze: {
    card: "bg-white border-b-[8px] border-orange-300 shadow-[0px_10px_40px_rgba(49,60,15,0.04)]",
    badge: "bg-orange-400 text-white border-white",
    medal: "text-orange-400",
    bar: "bg-orange-400",
  },
};

const formatXp = (xp) => `${Number(xp).toLocaleString("en-US")} XP`;
const hasAvatar = (value) => typeof value === "string" && value.trim().length > 0;

const LeaderboardPodiumCard = ({ entry, hero = false }) => {
  const accent = accentStyles[entry.accent];

  return (
    <article
      className={`relative rounded-[2rem] p-8 text-center transition-transform duration-300 hover:scale-[1.02] ${accent.card} ${
        hero ? "z-10 scale-100 md:scale-110" : ""
      }`}
      data-testid={`leaderboard-podium-${entry.rank}`}
    >
      {hero ? (
        <div className="absolute -top-9 left-1/2 -translate-x-1/2">
          <Crown weight="fill" size={58} className={accent.medal} />
        </div>
      ) : null}

      <div className="relative mb-6 inline-block">
        {hasAvatar(entry.avatar) ? (
          <img
            src={entry.avatar}
            alt={entry.name}
            className={`mx-auto rounded-full object-cover ${hero ? "h-32 w-32" : "h-24 w-24"} ${
              hero ? "bg-white/50 p-1" : "bg-slate-50 p-1"
            }`}
          />
        ) : (
          <div
            className={`mx-auto flex items-center justify-center rounded-full font-black uppercase ${
              hero ? "h-32 w-32 bg-white/50 text-4xl text-[#693a00]" : "h-24 w-24 bg-slate-100 text-3xl text-zinc-700"
            }`}
          >
            {entry.name.charAt(0)}
          </div>
        )}
        <div
          className={`absolute -bottom-2 -right-2 flex h-10 w-10 items-center justify-center rounded-full border-4 font-bold ${
            accent.badge
          } ${hero ? "h-12 w-12 text-xl" : ""}`}
        >
          {entry.rank}
        </div>
      </div>

      <h3 className={`font-display tracking-tight ${hero ? "text-4xl font-extrabold text-[#693a00]" : "truncate text-xl font-bold text-zinc-900"}`}>
        {entry.name}
      </h3>

      <div className={`mt-2 flex items-center justify-center gap-2 font-bold ${hero ? "text-[#693a00]" : "text-zinc-500"}`}>
        <Medal weight="fill" size={18} className={accent.medal} />
        {formatXp(entry.xp)}
      </div>

      {!hero ? (
        <div className="mt-5 h-2 w-full overflow-hidden rounded-full bg-zinc-200">
          <div className={`h-full rounded-full ${accent.bar}`} style={{ width: `${entry.progress}%` }} />
        </div>
      ) : null}
    </article>
  );
};

const LeaderboardPodium = ({ entries = [] }) => {
  const first = entries.find((entry) => entry.rank === 1);
  const second = entries.find((entry) => entry.rank === 2);
  const third = entries.find((entry) => entry.rank === 3);

  if (!first || !second || !third) {
    return null;
  }

  return (
    <section className="mb-14 grid grid-cols-1 items-end gap-8 md:grid-cols-3">
      <div className="order-2 md:order-1">
        <LeaderboardPodiumCard entry={second} />
      </div>
      <div className="order-1 md:order-2">
        <LeaderboardPodiumCard entry={first} hero />
      </div>
      <div className="order-3">
        <LeaderboardPodiumCard entry={third} />
      </div>
    </section>
  );
};

export default LeaderboardPodium;
