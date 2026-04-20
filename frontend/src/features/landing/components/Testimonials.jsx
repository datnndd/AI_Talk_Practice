import { motion } from "framer-motion";
import { Quotes, Star } from "@phosphor-icons/react";

const Testimonials = () => {
  const testimonials = [
    {
      name: "Marcus Chen",
      role: "Marketing Director, Singapore",
      content: "The AI feels surprisingly human. I used to be terrified of speaking, but now I look forward to my daily 15-minute French chats.",
      image: "https://picsum.photos/seed/marcusc/200/200"
    },
    {
      name: "Elena Rodriguez",
      role: "Software Engineer, Brazil",
      content: "LingoAI's business-specific tracks helped me land my dream job in Berlin. The roleplay practice felt focused and practical.",
      image: "https://picsum.photos/seed/elena/200/200"
    },
    {
      name: "Julian v. Berg",
      role: "PhD Researcher, Netherlands",
      content: "I've tried every app out there. This is the only one that actually forces you to speak rather than just tapping buttons.",
      image: "https://picsum.photos/seed/julian/200/200"
    }
  ];

  return (
    <section className="py-32 bg-white overflow-hidden" id="testimonials">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-24 space-y-4">
          <h2 className="text-4xl md:text-5xl font-black tracking-tighter text-zinc-900 font-display">
            Trusted by Global Learners
          </h2>
          <p className="text-zinc-500 text-lg font-medium max-w-2xl mx-auto">
            See how LingoAI is transforming lives across the globe.
          </p>
          <div className="flex items-center justify-center gap-4 mt-8">
            <div className="flex items-center gap-1 text-primary">
              {[1, 2, 3, 4, 5].map((i) => (
                <Star key={i} weight="fill" size={20} />
              ))}
            </div>
            <span className="font-bold text-zinc-900 border-l border-zinc-200 pl-4">4.9/5 Average Rating</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          {testimonials.map((t, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.2, duration: 0.8 }}
              className={`p-10 rounded-[2.5rem] bg-[#f9fafb] border border-slate-200/50 flex flex-col justify-between hover:bg-white hover:shadow-2xl transition-all duration-500 group ${
                i === 1 ? "md:translate-y-12" : i === 2 ? "md:translate-y-24" : ""
              }`}
            >
              <div className="space-y-6">
                <Quotes weight="fill" size={48} className="text-primary opacity-20 transition-opacity group-hover:opacity-40" />
                <p className="text-lg leading-relaxed text-zinc-700 font-medium italic">
                  "{t.content}"
                </p>
              </div>
              
              <div className="mt-12 flex items-center gap-4">
                <img
                  alt={t.name}
                  className="w-14 h-14 rounded-full object-cover border-4 border-white shadow-diffusion"
                  src={t.image}
                />
                <div>
                  <h4 className="font-black text-zinc-900 font-display">{t.name}</h4>
                  <p className="text-xs text-zinc-500 font-bold uppercase tracking-widest">{t.role}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Testimonials;
