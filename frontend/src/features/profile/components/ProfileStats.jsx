import { CalendarCheck, Coins, Lightning, Star } from "@phosphor-icons/react";

const ProfileStats = ({ stats }) => {
  const statItems = [
    {
      label: "Level",
      value: stats.level || 1,
      Icon: Star,
      color: "#ff9600",
    },
    {
      label: "Total XP",
      value: stats.totalXp || 0,
      Icon: Lightning,
      color: "#1cb0f6",
    },
    {
      label: "Coin",
      value: stats.coin || 0,
      Icon: Coins,
      color: "#ff4b4b",
    },
    {
      label: "Check-in streak",
      value: stats.checkInStreak || 0,
      Icon: CalendarCheck,
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
