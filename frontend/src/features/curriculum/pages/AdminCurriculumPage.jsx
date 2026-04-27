import { useCallback, useEffect, useMemo, useState } from "react";
import { Plus, Sparkle } from "@phosphor-icons/react";
import AdminShell from "@/features/admin-scenarios/components/AdminShell";
import { adminCurriculumApi } from "@/features/curriculum/api/curriculumApi";

const EMPTY_CONTENT = {
  vocab_pronunciation: { words: [{ word: "hello", meaning_vi: "xin chào" }] },
  cloze_dictation: {
    passage: "I would like a ___, please.",
    blanks: [{ answer: "coffee", accepted_answers: ["coffee"], meaning_vi: "cà phê", explanation_vi: "Danh từ chỉ đồ uống." }],
  },
  sentence_pronunciation: { reference_text: "Could you help me with my reservation?" },
  interactive_conversation: { scenario_id: 1 },
};

const pretty = (value) => JSON.stringify(value, null, 2);

const AdminCurriculumPage = () => {
  const [levels, setLevels] = useState([]);
  const [selectedLevelId, setSelectedLevelId] = useState(null);
  const [selectedLessonId, setSelectedLessonId] = useState(null);
  const [levelForm, setLevelForm] = useState({ code: "", title: "", description: "", order_index: 0, is_active: true });
  const [lessonForm, setLessonForm] = useState({
    title: "",
    description: "",
    order_index: 0,
    estimated_minutes: 10,
    xp_reward: 50,
    coin_reward: 0,
    is_active: true,
  });
  const [exerciseForm, setExerciseForm] = useState({
    type: "vocab_pronunciation",
    title: "",
    order_index: 0,
    pass_score: 80,
    is_required: true,
    is_active: true,
    content: pretty(EMPTY_CONTENT.vocab_pronunciation),
  });
  const [dictionaryWords, setDictionaryWords] = useState("");
  const [dictionaryPreview, setDictionaryPreview] = useState([]);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const selectedLevel = useMemo(() => levels.find((item) => item.id === selectedLevelId), [levels, selectedLevelId]);
  const selectedLesson = useMemo(
    () => selectedLevel?.lessons?.find((item) => item.id === selectedLessonId),
    [selectedLevel, selectedLessonId],
  );

  const load = useCallback(async () => {
    setError("");
    try {
      const response = await adminCurriculumApi.listLevels();
      setLevels(response);
      setSelectedLevelId((current) => current || response[0]?.id || null);
      setSelectedLessonId((current) => current || response[0]?.lessons?.[0]?.id || null);
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể tải curriculum.");
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  const createLevel = async (event) => {
    event.preventDefault();
    try {
      await adminCurriculumApi.createLevel({ ...levelForm, order_index: Number(levelForm.order_index) });
      setLevelForm({ code: "", title: "", description: "", order_index: 0, is_active: true });
      setNotice("Đã tạo level.");
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể tạo level.");
    }
  };

  const createLesson = async (event) => {
    event.preventDefault();
    if (!selectedLevelId) return;
    try {
      await adminCurriculumApi.createLesson({
        ...lessonForm,
        level_id: selectedLevelId,
        order_index: Number(lessonForm.order_index),
        estimated_minutes: Number(lessonForm.estimated_minutes),
        xp_reward: Number(lessonForm.xp_reward),
        coin_reward: Number(lessonForm.coin_reward),
      });
      setLessonForm({
        title: "",
        description: "",
        order_index: 0,
        estimated_minutes: 10,
        xp_reward: 50,
        coin_reward: 0,
        is_active: true,
      });
      setNotice("Đã tạo lesson.");
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể tạo lesson.");
    }
  };

  const createExercise = async (event) => {
    event.preventDefault();
    if (!selectedLessonId) return;
    try {
      await adminCurriculumApi.createExercise({
        type: exerciseForm.type,
        title: exerciseForm.title,
        lesson_id: selectedLessonId,
        order_index: Number(exerciseForm.order_index),
        pass_score: Number(exerciseForm.pass_score),
        is_required: exerciseForm.is_required,
        is_active: exerciseForm.is_active,
        content: JSON.parse(exerciseForm.content || "{}"),
      });
      setExerciseForm((current) => ({ ...current, title: "", order_index: Number(current.order_index) + 1 }));
      setNotice("Đã tạo exercise.");
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || "Không thể tạo exercise.");
    }
  };

  const previewDictionary = async () => {
    try {
      const words = dictionaryWords.split(/\n|,/).map((item) => item.trim()).filter(Boolean);
      const response = await adminCurriculumApi.previewDictionary(words);
      setDictionaryPreview(response);
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể preview dictionary.");
    }
  };

  const updateExerciseType = (type) => {
    setExerciseForm((current) => ({
      ...current,
      type,
      content: pretty(EMPTY_CONTENT[type]),
    }));
  };

  return (
    <AdminShell
      title="Curriculum Admin"
      subtitle="Build levels, lessons, and exercise sequences for locked learning progress."
    >
      <div className="space-y-6">
        {(notice || error) && (
          <div className={`rounded-2xl px-4 py-3 text-sm font-semibold ${error ? "bg-rose-50 text-rose-700" : "bg-emerald-50 text-emerald-700"}`}>
            {error || notice}
          </div>
        )}

        <section className="grid gap-5 xl:grid-cols-[320px_1fr]">
          <div className="space-y-4 rounded-[28px] border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="text-xl font-black">Levels</h2>
            <div className="space-y-2">
              {levels.map((level) => (
                <button
                  key={level.id}
                  type="button"
                  onClick={() => {
                    setSelectedLevelId(level.id);
                    setSelectedLessonId(level.lessons?.[0]?.id || null);
                  }}
                  className={`w-full rounded-xl border px-3 py-3 text-left text-sm font-bold ${selectedLevelId === level.id ? "border-primary bg-primary/5" : "border-zinc-200"}`}
                >
                  {level.order_index}. {level.title}
                </button>
              ))}
            </div>
            <form onSubmit={createLevel} className="space-y-3 border-t border-zinc-200 pt-4">
              <input required value={levelForm.code} onChange={(e) => setLevelForm((f) => ({ ...f, code: e.target.value }))} placeholder="Code: A1" className="w-full rounded-xl border px-3 py-2 text-sm" />
              <input required value={levelForm.title} onChange={(e) => setLevelForm((f) => ({ ...f, title: e.target.value }))} placeholder="Level title" className="w-full rounded-xl border px-3 py-2 text-sm" />
              <input type="number" value={levelForm.order_index} onChange={(e) => setLevelForm((f) => ({ ...f, order_index: e.target.value }))} className="w-full rounded-xl border px-3 py-2 text-sm" />
              <button className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-black text-white"><Plus size={16} /> Add level</button>
            </form>
          </div>

          <div className="grid gap-5 xl:grid-cols-2">
            <div className="space-y-4 rounded-[28px] border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
              <h2 className="text-xl font-black">Lessons in {selectedLevel?.title || "level"}</h2>
              <div className="space-y-2">
                {(selectedLevel?.lessons || []).map((lesson) => (
                  <button
                    key={lesson.id}
                    type="button"
                    onClick={() => setSelectedLessonId(lesson.id)}
                    className={`w-full rounded-xl border px-3 py-3 text-left text-sm font-bold ${selectedLessonId === lesson.id ? "border-primary bg-primary/5" : "border-zinc-200"}`}
                  >
                    {lesson.order_index}. {lesson.title}
                    <span className="mt-1 block text-xs font-semibold text-zinc-500">
                      +{lesson.xp_reward || 0} XP · +{lesson.coin_reward || 0} Coin
                    </span>
                  </button>
                ))}
              </div>
              <form onSubmit={createLesson} className="space-y-3 border-t border-zinc-200 pt-4">
                <input required value={lessonForm.title} onChange={(e) => setLessonForm((f) => ({ ...f, title: e.target.value }))} placeholder="Lesson title" className="w-full rounded-xl border px-3 py-2 text-sm" />
                <textarea value={lessonForm.description} onChange={(e) => setLessonForm((f) => ({ ...f, description: e.target.value }))} placeholder="Lesson description" className="w-full rounded-xl border px-3 py-2 text-sm" />
                <div className="grid grid-cols-2 gap-2">
                  <input type="number" value={lessonForm.order_index} onChange={(e) => setLessonForm((f) => ({ ...f, order_index: e.target.value }))} className="rounded-xl border px-3 py-2 text-sm" />
                  <input type="number" value={lessonForm.estimated_minutes} onChange={(e) => setLessonForm((f) => ({ ...f, estimated_minutes: e.target.value }))} className="rounded-xl border px-3 py-2 text-sm" />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <input type="number" min="0" value={lessonForm.xp_reward} onChange={(e) => setLessonForm((f) => ({ ...f, xp_reward: e.target.value }))} placeholder="XP reward" className="rounded-xl border px-3 py-2 text-sm" />
                  <input type="number" min="0" value={lessonForm.coin_reward} onChange={(e) => setLessonForm((f) => ({ ...f, coin_reward: e.target.value }))} placeholder="Coin reward" className="rounded-xl border px-3 py-2 text-sm" />
                </div>
                <button className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-black text-white"><Plus size={16} /> Add lesson</button>
              </form>
            </div>

            <div className="space-y-4 rounded-[28px] border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
              <h2 className="text-xl font-black">Exercises in {selectedLesson?.title || "lesson"}</h2>
              <div className="space-y-2">
                {(selectedLesson?.exercises || []).map((exercise) => (
                  <div key={exercise.id} className="rounded-xl border border-zinc-200 px-3 py-3 text-sm">
                    <p className="font-black">{exercise.order_index}. {exercise.title}</p>
                    <p className="mt-1 text-xs font-semibold text-zinc-500">{exercise.type} · pass {exercise.pass_score}</p>
                  </div>
                ))}
              </div>
              <form onSubmit={createExercise} className="space-y-3 border-t border-zinc-200 pt-4">
                <select value={exerciseForm.type} onChange={(e) => updateExerciseType(e.target.value)} className="w-full rounded-xl border px-3 py-2 text-sm">
                  <option value="vocab_pronunciation">Vocabulary pronunciation</option>
                  <option value="cloze_dictation">Cloze dictation</option>
                  <option value="sentence_pronunciation">Sentence pronunciation</option>
                  <option value="interactive_conversation">Interactive conversation</option>
                </select>
                <input required value={exerciseForm.title} onChange={(e) => setExerciseForm((f) => ({ ...f, title: e.target.value }))} placeholder="Exercise title" className="w-full rounded-xl border px-3 py-2 text-sm" />
                <div className="grid grid-cols-2 gap-2">
                  <input type="number" value={exerciseForm.order_index} onChange={(e) => setExerciseForm((f) => ({ ...f, order_index: e.target.value }))} className="rounded-xl border px-3 py-2 text-sm" />
                  <input type="number" value={exerciseForm.pass_score} onChange={(e) => setExerciseForm((f) => ({ ...f, pass_score: e.target.value }))} className="rounded-xl border px-3 py-2 text-sm" />
                </div>
                <textarea value={exerciseForm.content} onChange={(e) => setExerciseForm((f) => ({ ...f, content: e.target.value }))} rows={8} className="w-full rounded-xl border px-3 py-2 font-mono text-xs" />
                <button className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-black text-white"><Plus size={16} /> Add exercise</button>
              </form>
            </div>
          </div>
        </section>

        <section className="rounded-[28px] border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="text-xl font-black">Dictionary Preview</h2>
          <div className="mt-3 flex flex-col gap-3 md:flex-row">
            <textarea value={dictionaryWords} onChange={(e) => setDictionaryWords(e.target.value)} placeholder="hello&#10;reservation" className="min-h-24 flex-1 rounded-xl border px-3 py-2 text-sm" />
            <button type="button" onClick={previewDictionary} className="inline-flex items-center justify-center gap-2 rounded-xl bg-zinc-950 px-4 py-2 text-sm font-black text-white">
              <Sparkle size={16} /> Preview
            </button>
          </div>
          {dictionaryPreview.length > 0 && (
            <div className="mt-4 grid gap-2 md:grid-cols-2">
              {dictionaryPreview.map((term) => (
                <div key={term.normalized_word} className="rounded-xl border border-zinc-200 p-3 text-sm">
                  <p className="font-black">{term.word}</p>
                  <p className="text-zinc-600">{term.meaning_vi || "Chưa có nghĩa tiếng Việt trong cache."}</p>
                  <p className="text-xs text-zinc-500">{term.ipa || ""}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </AdminShell>
  );
};

export default AdminCurriculumPage;
