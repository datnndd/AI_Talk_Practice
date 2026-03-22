import { motion } from "framer-motion";
import { MicrophoneSlash, VideoCameraSlash } from "@phosphor-icons/react";

const CameraOverlay = () => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="absolute top-6 left-6 w-1/3 aspect-[16/10] rounded-2xl overflow-hidden z-20 border border-white/40 shadow-2xl glass-panel group"
    >
      <div className="absolute top-3 left-3 bg-rose-500 text-white px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider flex items-center gap-1.5 z-10">
        <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
        Live
      </div>
      
      <img 
        src="https://picsum.photos/seed/student_webcam/400/250" 
        alt="Student Webcam" 
        className="w-full h-full object-cover opacity-90 transition-opacity group-hover:opacity-100"
      />
      
      <div className="absolute bottom-3 right-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <button className="p-2 bg-black/40 backdrop-blur-md text-white rounded-lg hover:bg-black/60 transition-colors">
          <MicrophoneSlash size={16} />
        </button>
        <button className="p-2 bg-black/40 backdrop-blur-md text-white rounded-lg hover:bg-black/60 transition-colors">
          <VideoCameraSlash size={16} />
        </button>
      </div>
    </motion.div>
  );
};

export default CameraOverlay;
