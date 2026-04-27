import { Fire, Lightning, Trophy, Medal } from "@phosphor-icons/react";

const ProfileStats = ({ stats }) => {
  const statItems = [
    {
      label: "Day streak",
      value: stats.streak || 0,
      Icon: Fire,
      color: "#ff9600",
    },
    {
      label: "Total XP",
      value: stats.totalXp || 0,
      Icon: Lightning,
      color: "#1cb0f6",
    },
    {
      label: "Current league",
      value: stats.league || "Bronze",
      Icon: Trophy,
      color: "#ff4b4b",
    },
    {
      label: "Top 3 finishes",
      value: stats.topFinishes || 0,
      Icon: Medal,
      color: "#ffc800",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4">
      {statItems.map(({ Icon, ...item }) => (
        <div 
          key={item.label}
          className="flex items-center gap-4 rounded-2xl border-2 border-[#e5e5e5] p-4 transition-transform hover:scale-[1.02]"
        >
          <Icon size={40} weight="fill" color={item.color} className="shrink-0" />
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
