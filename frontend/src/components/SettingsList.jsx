import { motion } from "framer-motion";
import { Bell, Lock, Shield, CaretRight } from "@phosphor-icons/react";
import { useState } from "react";

const SettingItem = ({ icon: Icon, color, label, sublabel, type = "link" }) => {
  const [active, setActive] = useState(true);

  return (
    <div className="flex items-center justify-between p-4 hover:bg-zinc-50 rounded-3xl transition-all cursor-pointer group">
      <div className="flex items-center gap-4">
        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-transform group-hover:scale-110 ${color}`}>
          <Icon weight="bold" size={24} />
        </div>
        <div>
          <p className="font-bold text-zinc-950 text-sm">{label}</p>
          <p className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider">{sublabel}</p>
        </div>
      </div>
      
      {type === "toggle" ? (
        <div 
          onClick={() => setActive(!active)}
          className={`w-12 h-6 rounded-full p-1 transition-colors duration-300 relative ${active ? 'bg-primary' : 'bg-zinc-200'}`}
        >
          <motion.div 
            animate={{ x: active ? 24 : 0 }}
            className="w-4 h-4 bg-white rounded-full shadow-sm"
          />
        </div>
      ) : (
        <CaretRight weight="bold" className="text-zinc-300 group-hover:text-primary group-hover:translate-x-1 transition-all" />
      )}
    </div>
  );
};

const SettingsList = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="md:col-span-7 bg-white border border-zinc-200 rounded-[2.5rem] p-8 shadow-sm hover:shadow-xl transition-all duration-300"
    >
      <h3 className="font-bold text-lg text-zinc-950 font-display mb-8">Account Settings</h3>
      <div className="space-y-4">
        <SettingItem 
          icon={Bell} 
          color="bg-blue-50 text-blue-600" 
          label="Notifications" 
          sublabel="Alerts & Sounds" 
          type="toggle"
        />
        <SettingItem 
          icon={Lock} 
          color="bg-purple-50 text-purple-600" 
          label="Privacy" 
          sublabel="Visibility" 
        />
        <SettingItem 
          icon={Shield} 
          color="bg-rose-50 text-rose-600" 
          label="Security" 
          sublabel="Password & 2FA" 
        />
      </div>
    </motion.div>
  );
};

export default SettingsList;
