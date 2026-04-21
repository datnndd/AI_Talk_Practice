const formatXp = (xp) => `${Number(xp).toLocaleString("en-US")} XP`;
const hasAvatar = (value) => typeof value === "string" && value.trim().length > 0;
const formatRank = (rank) => (Number(rank) > 9999 ? "10k+" : rank);

const ActivityBars = ({ tone = "green" }) => {
  const bars = tone === "green"
    ? ["h-3 bg-[#58CC02]", "h-4 bg-[#58CC02]", "h-2 bg-[#58CC02]", "h-5 bg-[#8ff25b]", "h-3 bg-[#8ff25b]"]
    : ["h-4 bg-[#58CC02]", "h-2 bg-[#58CC02]", "h-5 bg-[#58CC02]", "h-3 bg-[#8ff25b]"];

  return (
    <div className="flex gap-0.5">
      {bars.map((barClass, index) => (
        <div key={`${tone}-${index}`} className={`w-1 rounded-full ${barClass}`} />
      ))}
    </div>
  );
};

const LeaderboardRow = ({ entry }) => (
  <article
    className="flex items-center gap-4 rounded-[1.75rem] bg-white px-4 py-5 shadow-[0px_10px_40px_rgba(49,60,15,0.04)] transition-colors duration-200 hover:bg-[#fbfdf6] md:gap-6 md:px-6"
    data-testid={`leaderboard-row-${entry.rank}`}
  >
    <div className="w-8 text-2xl font-black text-zinc-600">{entry.rank}</div>

    <div className="relative">
      {hasAvatar(entry.avatar) ? (
        <img src={entry.avatar} alt={entry.name} className="h-14 w-14 rounded-full object-cover" />
      ) : (
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 text-lg font-black text-zinc-700">
          {entry.name.charAt(0).toUpperCase()}
        </div>
      )}
      <span className="absolute -bottom-1 -right-1 text-lg">{entry.country}</span>
    </div>

    <div className="min-w-0 flex-1">
      <h4 className="truncate text-lg font-bold text-zinc-900">{entry.name}</h4>
      <div className="flex items-center gap-3">
        <ActivityBars />
        <span className="text-sm font-bold text-zinc-500">{formatXp(entry.xp)}</span>
      </div>
    </div>

    <div className="flex items-center gap-1 text-sm font-black text-[#ffb4b0]">
      <span>🔥</span>
      <span>{entry.streak}</span>
    </div>
  </article>
);

const CurrentUserRow = ({ entry }) => (
  <article
    className="flex items-center gap-4 rounded-[1.75rem] border-2 border-[#87fe45] bg-[#f5f7f1] px-4 py-6 ring-4 ring-[#87fe45]/20 md:gap-6 md:px-6"
    data-testid="leaderboard-current-user"
  >
    <div className="w-12 text-xl font-black text-[#2b6c00]">{formatRank(entry.rank)}</div>

    <div className="relative">
      {entry.avatar ? (
        <img src={entry.avatar} alt={entry.name} className="h-14 w-14 rounded-full object-cover" />
      ) : (
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-white text-lg font-black text-[#2b6c00]">
          {entry.name.charAt(0).toUpperCase()}
        </div>
      )}
      <span className="absolute -bottom-1 -right-1 text-lg">{entry.country}</span>
    </div>

    <div className="min-w-0 flex-1">
      <h4 className="truncate text-lg font-bold text-zinc-900">
      {entry.name}
        {entry.encouragement ? (
          <span className="ml-2 text-sm font-medium text-zinc-400">({entry.encouragement})</span>
        ) : null}
      </h4>
      <div className="flex items-center gap-3">
        <span className="text-[#58CC02]">✦</span>
        <span className="text-sm font-bold text-zinc-500">{formatXp(entry.xp)}</span>
      </div>
    </div>

    <div className="flex items-center gap-1 text-sm font-black text-zinc-500">
      <span className="opacity-20">🔥</span>
      <span>{entry.streak}</span>
    </div>
  </article>
);

const LeaderboardList = ({ entries = [], currentUser }) => {
  return (
    <section className="space-y-4">
      {entries
        .filter((entry) => entry.rank > 3)
        .map((entry) => (
          <LeaderboardRow key={entry.id} entry={entry} />
        ))}

      <div className="py-4">
        <div className="flex justify-center gap-2">
          {[0, 1, 2].map((index) => (
            <span key={index} className="h-2 w-2 rounded-full bg-[#becbb1]" />
          ))}
        </div>
      </div>

      {currentUser ? <CurrentUserRow entry={currentUser} /> : null}
    </section>
  );
};

export default LeaderboardList;
