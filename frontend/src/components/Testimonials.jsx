import { motion } from "framer-motion";
import { Star } from "@phosphor-icons/react";

const Testimonials = () => {
  const testimonials = [
    {
      name: "Marcus Aurelius",
      role: "Learning Spanish & Italian",
      content: "The real-time feedback is a game changer. I've used every app on the market, but nothing compares to actually speaking with LingoAI's tutors.",
      image: "https://picsum.photos/seed/marcus/100/100"
    },
    {
      name: "Sienna Rivers",
      role: "Learning German",
      content: "I went from zero to being able to order dinner in Berlin within 3 weeks. The AI's patience is what makes it so much less stressful than human tutors.",
      image: "https://picsum.photos/seed/sienna/100/100"
    },
    {
      name: "Kaito Nakamura",
      role: "Learning Japanese",
      content: "The Bento-style dashboard makes it so easy to see my progress. I love how it tracks my 'confidence score' for different conversation topics.",
      image: "https://picsum.photos/seed/kaito/100/100"
    }
  ];

  return (
    <section className="py-24 overflow-hidden bg-white">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-6">
          <div>
            <h2 className="text-4xl font-bold tracking-tight text-zinc-950 mb-2 font-display">Loved by polyglots</h2>
            <p className="text-zinc-500 text-lg font-medium">Real stories from our global community of learners.</p>
          </div>
          <div className="flex items-center gap-4 bg-zinc-50 px-6 py-4 rounded-2xl border border-zinc-100">
            <div className="flex items-center gap-1 text-primary">
              {[1, 2, 3, 4, 5].map((i) => (
                <Star key={i} weight="fill" size={20} />
              ))}
            </div>
            <span className="font-bold text-zinc-900">4.9/5 Average Rating</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-start">
          {testimonials.map((t, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className={`p-8 rounded-3xl bg-zinc-50/50 border border-zinc-100 flex flex-col hover:bg-white hover:shadow-xl hover:-translate-y-1 transition-all duration-500 ${
                i === 1 ? "md:mt-12" : i === 2 ? "md:mt-24" : ""
              }`}
            >
              <div className="flex items-center gap-4 mb-6">
                <img
                  alt={t.name}
                  className="w-12 h-12 rounded-full object-cover border-2 border-white shadow-sm"
                  src={t.image}
                />
                <div>
                  <h4 className="font-bold text-zinc-900">{t.name}</h4>
                  <p className="text-xs text-zinc-500 font-medium uppercase tracking-wider">{t.role}</p>
                </div>
              </div>
              <p className="text-zinc-600 leading-relaxed italic font-medium">
                "{t.content}"
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Testimonials;
