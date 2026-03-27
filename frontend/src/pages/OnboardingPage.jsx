import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { PaperPlaneRight, User, Robot } from "@phosphor-icons/react";

const OnboardingPage = () => {
  const { onboard } = useAuth();
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);

  const [step, setStep] = useState(0);
  const [messages, setMessages] = useState([
    {
      role: "bot",
      content: "Xin chào, tôi là AI Talk Practice, còn bạn là ...?",
    },
  ]);
  const [formData, setFormData] = useState({
    display_name: "",
    native_language: "vi",
    avatar: "user1",
    age: "",
    level: "beginner",
    learning_purpose: "",
    main_challenge: "",
    favorite_topics: [],
    daily_goal: 15,
  });

  const [inputValue, setInputValue] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addBotMessage = (text) => {
    setMessages((prev) => [...prev, { role: "bot", content: text }]);
  };

  const addUserMessage = (text) => {
    setMessages((prev) => [...prev, { role: "user", content: text }]);
  };

  const handleNextStep = async (value, displayValue) => {
    addUserMessage(displayValue || value);
    
    let updatedFormData = { ...formData };
    
    // Save to formData based on step
    switch (step) {
      case 0:
        updatedFormData.display_name = value;
        setTimeout(() => addBotMessage(`Chào ${value}! Ngôn ngữ mẹ đẻ của bạn là gì?`), 500);
        break;
      case 1:
        updatedFormData.native_language = value;
        setTimeout(() => addBotMessage("Tuyệt vời. Bạn có thể chọn một avatar nhé!"), 500);
        break;
      case 2:
        updatedFormData.avatar = value;
        setTimeout(() => addBotMessage("Tuổi của bạn là bao nhiêu?"), 500);
        break;
      case 3:
        updatedFormData.age = parseInt(value, 10);
        setTimeout(() => addBotMessage("Trình độ tiếng Anh hiện tại của bạn là gì?"), 500);
        break;
      case 4:
        updatedFormData.level = value;
        setTimeout(() => addBotMessage("Tại sao bạn lại muốn học tiếng Anh?"), 500);
        break;
      case 5:
        updatedFormData.learning_purpose = value;
        setTimeout(() => addBotMessage("Thử thách lớn nhất của bạn khi học là gì?"), 500);
        break;
      case 6:
        updatedFormData.main_challenge = value;
        setTimeout(() => addBotMessage("Hãy chọn 3 chủ đề bạn yêu thích nhé! (vd: Travel, Culture, Technology)"), 500);
        break;
      case 7:
        // Assume comma separated
        updatedFormData.favorite_topics = value.split(",").map(s => s.trim()).filter(Boolean).join(", ");
        setTimeout(() => addBotMessage("Cuối cùng, mục tiêu luyện tập hàng ngày của bạn là bao nhiêu phút?"), 500);
        break;
      case 8:
        updatedFormData.daily_goal = parseInt(value, 10) || 15;
        setTimeout(() => addBotMessage("Cảm ơn bạn! Đang thiết lập hồ sơ..."), 500);
        // Finish onboarding
        finishOnboarding(updatedFormData);
        break;
      default:
        break;
    }
    
    setFormData(updatedFormData);
    setStep((prev) => prev + 1);
    setInputValue("");
  };

  const finishOnboarding = async (finalData) => {
    setIsSubmitting(true);
    try {
      await onboard({
        display_name: finalData.display_name,
        native_language: finalData.native_language,
        avatar: finalData.avatar,
        age: finalData.age,
        level: finalData.level,
        learning_purpose: finalData.learning_purpose,
        main_challenge: finalData.main_challenge,
        favorite_topics: finalData.favorite_topics,
        daily_goal: finalData.daily_goal,
      });
      navigate("/topics");
    } catch (err) {
      console.error(err);
      addBotMessage("Sorry, có lỗi xảy ra. Vui lòng thử lại sau.");
      setIsSubmitting(false);
    }
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isSubmitting) return;
    handleNextStep(inputValue);
  };

  // Render input controls based on current step
  const renderInputControls = () => {
    if (isSubmitting || step > 8) {
      return (
        <div className="flex justify-center p-4">
          <div className="animate-pulse bg-primary/20 text-primary px-4 py-2 rounded-full text-sm font-bold">
            Creating your profile...
          </div>
        </div>
      );
    }

    switch (step) {
      case 0: // Name
      case 3: // Age
      case 5: // Purpose
      case 6: // Challenge
      case 7: // Topics
      case 8: // Daily Goal
        return (
          <form onSubmit={handleTextSubmit} className="flex gap-2 bg-white p-2 rounded-2xl shadow-sm border border-zinc-100">
            <input
              type={step === 3 || step === 8 ? "number" : "text"}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={
                step === 0 ? "Nhập tên của bạn..." :
                step === 3 ? "Tuổi..." :
                step === 7 ? "Nhập các chủ đề, cách nhau bởi dấu phẩy..." :
                step === 8 ? "Số phút (vd: 15)..." :
                "Nhập câu trả lời của bạn..."
              }
              className="flex-1 bg-transparent px-4 py-3 outline-none font-medium text-zinc-900 placeholder:text-zinc-400"
              autoFocus
            />
            <button 
              type="submit" 
              disabled={!inputValue.trim()}
              className="bg-primary text-white p-3 rounded-xl hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              <PaperPlaneRight weight="fill" size={20} />
            </button>
          </form>
        );

      case 1: // Native Language
        return (
          <div className="grid grid-cols-2 gap-3">
            {[
              { id: "vi", label: "Tiếng Việt 🇻🇳" },
              { id: "en", label: "English 🇺🇸" },
              { id: "es", label: "Español 🇪🇸" },
              { id: "zh", label: "Chinese 🇨🇳" },
            ].map((lang) => (
              <button
                key={lang.id}
                onClick={() => handleNextStep(lang.id, lang.label)}
                className="bg-white border border-zinc-200 p-4 rounded-2xl font-bold text-zinc-700 hover:border-primary hover:text-primary transition-colors text-sm"
              >
                {lang.label}
              </button>
            ))}
          </div>
        );

      case 2: // Avatar
        return (
          <div className="flex gap-4 overflow-x-auto pb-2 px-2 snap-x">
            {["👨‍💻", "👩‍💻", "🦊", "🐼", "🤖", "👻"].map((emoji, idx) => (
              <button
                key={idx}
                onClick={() => handleNextStep(emoji, `Chọn Avatar ${emoji}`)}
                className="flex-shrink-0 w-16 h-16 bg-white border border-zinc-200 rounded-full text-3xl flex items-center justify-center hover:border-primary hover:bg-primary/5 transition-all snap-center"
              >
                {emoji}
              </button>
            ))}
          </div>
        );

      case 4: // Level
        return (
          <div className="flex flex-col gap-3">
            {[
              { id: "beginner", label: "Beginner", desc: "Mới bắt đầu học" },
              { id: "intermediate", label: "Intermediate", desc: "Đã có thể giao tiếp cơ bản" },
              { id: "advanced", label: "Advanced", desc: "Sử dụng thành thạo" },
            ].map((lvl) => (
              <button
                key={lvl.id}
                onClick={() => handleNextStep(lvl.id, lvl.label)}
                className="bg-white border border-zinc-200 p-4 rounded-2xl text-left hover:border-primary hover:shadow-md transition-all group"
              >
                <div className="font-bold text-zinc-900 group-hover:text-primary">{lvl.label}</div>
                <div className="text-xs text-zinc-500 font-medium mt-1">{lvl.desc}</div>
              </button>
            ))}
          </div>
        );
        
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 flex flex-col font-sans">
      <header className="bg-white px-6 py-4 border-b border-zinc-100 flex items-center justify-between sticky top-0 z-10 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center text-primary">
            <Robot weight="fill" size={24} />
          </div>
          <div>
            <h1 className="font-bold text-zinc-900 text-sm">LingoFlow Onboarding</h1>
            <p className="text-xs text-zinc-500 font-medium">Bắt đầu hành trình của bạn</p>
          </div>
        </div>
        <div className="text-xs font-bold text-zinc-400">
          {Math.min(step + 1, 9)} / 9
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 flex flex-col gap-6 max-w-3xl mx-auto w-full">
        <AnimatePresence initial={false}>
          {messages.map((msg, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
              className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`flex gap-3 max-w-[85%] md:max-w-[75%] ${
                  msg.role === "user" ? "flex-row-reverse" : "flex-row"
                }`}
              >
                <div 
                  className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
                    msg.role === "user" ? "bg-zinc-200 text-zinc-600" : "bg-primary text-white"
                  }`}
                >
                  {msg.role === "user" ? <User weight="fill" size={16} /> : <Robot weight="fill" size={16} />}
                </div>
                <div
                  className={`px-5 py-3.5 rounded-2xl text-[15px] leading-relaxed font-medium shadow-sm ${
                    msg.role === "user"
                      ? "bg-primary text-white rounded-tr-sm"
                      : "bg-white text-zinc-800 border border-zinc-100 rounded-tl-sm"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={messagesEndRef} className="h-4" />
      </main>

      <footer className="bg-zinc-50/80 backdrop-blur-md p-4 md:p-6 border-t border-zinc-200 sticky bottom-0">
        <div className="max-w-3xl mx-auto">
          {renderInputControls()}
        </div>
      </footer>
    </div>
  );
};

export default OnboardingPage;
