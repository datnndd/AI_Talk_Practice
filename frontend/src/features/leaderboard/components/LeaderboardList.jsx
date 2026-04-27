import { Link } from "react-router-dom";
import { ArrowDown, Medal, Star } from "@phosphor-icons/react";
import "./Leaderboard.css";

const MEDAL_COLORS = {
  1: "#ffc800",
  2: "#b8c2cc",
  3: "#d97706",
};

const PromotionZone = () => (
  <div className="zone-separator promotion-zone border-y-2 border-[#e5e5e5] my-2">
    <Star size={18} weight="fill" className="zone-icon" />
    Promotion Zone
    <Star size={18} weight="fill" className="zone-icon" />
  </div>
);

const DemotionZone = () => (
  <div className="zone-separator demotion-zone border-y-2 border-[#e5e5e5] my-2">
    <ArrowDown size={18} weight="bold" className="zone-icon" />
    Demotion Zone
    <ArrowDown size={18} weight="bold" className="zone-icon" />
  </div>
);

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
  const PROMOTION_THRESHOLD = 5;
  const DEMOTION_START = 16; 

  return (
    <div className="leaderboard-list">
      {entries.map((entry, index) => {
        const isCurrentUser = currentUser?.id === entry.id;
        const elements = [];

        if (index === PROMOTION_THRESHOLD) {
          elements.push(<PromotionZone key="promotion-zone" />);
        }

        if (index === DEMOTION_START - 1) {
          elements.push(<DemotionZone key="demotion-zone" />);
        }

        elements.push(
          <LeaderboardRow 
            key={entry.id || index} 
            entry={entry} 
            isCurrentUser={isCurrentUser} 
          />
        );

        return elements;
      })}
    </div>
  );
};
export default LeaderboardList;
