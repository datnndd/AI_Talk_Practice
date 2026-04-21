const ACHIEVEMENT_ITEMS = [
  {
    id: "wildfire",
    name: "Wildfire",
    description: "Reach a 125 day streak",
    current: 80,
    total: 125,
    level: 7,
    icon: "https://friends.duolingo.com/kudos/assets/kudos_reaction_congrats.svg", // Placeholder icon
    color: "#ffc800",
  },
  {
    id: "sage",
    name: "Sage",
    description: "Earn 12500 XP",
    current: 10876,
    total: 12500,
    level: 8,
    icon: "https://friends.duolingo.com/kudos/assets/kudos_reaction_congrats.svg",
    color: "#ffc800",
  },
  {
    id: "champion",
    name: "Champion",
    description: "Advance to the Obsidian League",
    current: 8,
    total: 9,
    level: 9,
    icon: "https://friends.duolingo.com/kudos/assets/kudos_reaction_congrats.svg",
    color: "#ffc800",
  },
];

const ProfileAchievements = () => {
  return (
    <div className="space-y-4">
      {ACHIEVEMENT_ITEMS.map((item) => (
        <div key={item.id} className="flex gap-4 rounded-2xl border-2 border-[#e5e5e5] p-6 transition-transform hover:scale-[1.01]">
          {/* Badge Circle */}
          <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-full bg-[#f7f7f7] border-2 border-[#e5e5e5] relative">
             <div className="absolute -top-2 bg-yellow-400 text-white text-[10px] font-black px-2 py-0.5 rounded-lg border-2 border-white uppercase">
                Level {item.level}
             </div>
             <img src={item.icon} alt={item.name} className="h-10 w-10" />
          </div>

          <div className="flex flex-1 flex-col justify-center">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-xl font-black text-[#4b4b4b]">{item.name}</h3>
              <span className="text-sm font-bold text-[#afafaf] uppercase tracking-wide">
                {item.current}/{item.total}
              </span>
            </div>
            
            {/* Progress Bar */}
            <div className="h-4 w-full overflow-hidden rounded-full bg-[#e5e5e5]">
              <div 
                className="h-full rounded-full transition-all duration-1000"
                style={{ 
                  width: `${(item.current / item.total) * 100}%`,
                  backgroundColor: item.color 
                }}
              />
            </div>
            
            <p className="mt-2 text-sm font-bold text-[#777777]">{item.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ProfileAchievements;
