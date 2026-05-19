import { Link } from "react-router-dom";
import { Medal } from "@phosphor-icons/react";
import "./Leaderboard.css";

const MEDAL_COLORS = {
  1: "#ffc800",
  2: "#b8c2cc",
  3: "#d97706",
};

const LeaderboardRow = ({ entry, isCurrentUser }) => {
  const isMedalRank = entry.rank >= 1 && entry.rank <= 3;
  
  return (
    <Link 
      to={`/u/${entry.id}`} 
      className={`leaderboard-row ${isCurrentUser ? "leaderboard-row-current" : ""}`}
    >
      <div className="rank-indicator">
        {isMedalRank ? (
          <Medal size={30} weight="fill" color={MEDAL_COLORS[entry.rank]} className="medal-icon" />
        ) : (
          entry.rank
        )}
      </div>
      
      <div className="user-avatar-container">
        {entry.avatar ? (
          <img src={entry.avatar} className="user-avatar" alt={entry.name} />
        ) : (
          <div className="user-avatar flex items-center justify-center bg-zinc-100 text-[#4b4b4b]">
            {entry.name.charAt(0).toUpperCase()}
          </div>
        )}
      </div>

      <div className="user-name truncate">{entry.name}</div>
      
      <div className="user-xp">{entry.xp} XP</div>
    </Link>
  );
};

const LeaderboardList = ({ entries = [], currentUser }) => {
  const topEntries = entries.slice(0, 5);

  return (
    <div className="leaderboard-list">
      <section className="leaderboard-card" aria-labelledby="leaderboard-top-title">
        <div className="leaderboard-card-header">
          <p id="leaderboard-top-title" className="leaderboard-card-title">Top 5 Learners</p>
          <span className="leaderboard-card-badge">Weekly XP</span>
        </div>

        <div className="leaderboard-card-body">
          {topEntries.length > 0 ? (
            topEntries.map((entry, index) => (
              <LeaderboardRow
                key={entry.id || index}
                entry={entry}
                isCurrentUser={currentUser?.id === entry.id}
              />
            ))
          ) : (
            <div className="leaderboard-empty">No leaderboard data yet.</div>
          )}
        </div>
      </section>

      <section className="leaderboard-card leaderboard-current-card" aria-labelledby="leaderboard-current-title">
        <div className="leaderboard-card-header">
          <p id="leaderboard-current-title" className="leaderboard-card-title">Your Rank</p>
          <span className="leaderboard-card-badge leaderboard-card-badge-current">Current</span>
        </div>

        <div className="leaderboard-card-body">
          {currentUser ? (
            <LeaderboardRow entry={currentUser} isCurrentUser />
          ) : (
            <div className="leaderboard-empty">Your rank is not available yet.</div>
          )}
        </div>
      </section>
    </div>
  );
};
export default LeaderboardList;
