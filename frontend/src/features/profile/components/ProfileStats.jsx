import { Fire, Lightning, Trophy, Medal } from "@phosphor-icons/react";

const ProfileStats = ({ stats }) => {
  const statItems = [
    {
      label: "Day streak",
      value: stats.streak || 0,
      icon: "https://d35aaqx5ub95lt.cloudfront.net/images/icons/ba95e6081679d9d7e8c132da5cfce1ec.svg",
    },
    {
      label: "Total XP",
      value: stats.totalXp || 0,
      icon: "https://d35aaqx5ub95lt.cloudfront.net/images/profile/01ce3a817dd01842581c3d18debcbc46.svg",
    },
    {
      label: "Current league",
      value: stats.league || "Bronze",
      icon: "https://d35aaqx5ub95lt.cloudfront.net/images/leagues/74d6ab6e5b6f92e7d16a4a6664d1fafd.svg",
    },
    {
      label: "Top 3 finishes",
      value: stats.topFinishes || 0,
      icon: "https://d35aaqx5ub95lt.cloudfront.net/images/profile/3f97ae337724f7edb6dfbef23cd3a6e7.svg",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4">
      {statItems.map((item) => (
        <div 
          key={item.label}
          className="flex items-center gap-4 rounded-2xl border-2 border-[#e5e5e5] p-4 transition-transform hover:scale-[1.02]"
        >
          <img src={item.icon} alt={item.label} className="h-10 w-10 shrink-0" />
          <div>
            <div className="text-xl font-black text-[#4b4b4b]">{item.value}</div>
            <div className="text-sm font-bold text-[#afafaf] uppercase tracking-wide">{item.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ProfileStats;
