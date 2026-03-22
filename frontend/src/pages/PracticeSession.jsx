import { motion } from "framer-motion";
import ChatWindow from "../components/ChatWindow";
import MetricsSidebar from "../components/MetricsSidebar";
import TypewriterInput from "../components/TypewriterInput";

const PracticeSession = () => {
  return (
    <div className="min-h-[100dvh] bg-gradient-to-br from-blue-50 to-indigo-50 p-6 md:p-10 flex items-center justify-center font-sans antialiased">
      <main className="w-full max-w-[1440px] h-[calc(100dvh-80px)] grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-8 flex flex-col gap-6 h-full relative">
          <ChatWindow />
          <TypewriterInput />
        </div>
        
        <MetricsSidebar />
      </main>
    </div>
  );
};

export default PracticeSession;
