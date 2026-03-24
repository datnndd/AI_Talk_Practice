import { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import { api } from "../contexts/AuthContext";

const AdminScenarios = () => {
  const [scenarios, setScenarios] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    learning_objectives: "",
    ai_system_prompt: "",
    category: "Travel",
    difficulty: "medium"
  });

  useEffect(() => {
    fetchScenarios();
  }, []);

  const fetchScenarios = async () => {
    try {
      const response = await api.get("/scenarios");
      setScenarios(response.data);
    } catch (error) {
      console.error("Failed to fetch scenarios", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await api.put(`/scenarios/${editingId}`, formData);
      } else {
        await api.post("/scenarios", formData);
      }
      setIsModalOpen(false);
      resetForm();
      fetchScenarios();
    } catch (error) {
      console.error("Failed to save scenario", error);
      alert("Error saving scenario");
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm("Are you sure you want to delete this scenario?")) {
      try {
        await api.delete(`/scenarios/${id}`);
        fetchScenarios();
      } catch (error) {
        console.error("Failed to delete scenario", error);
      }
    }
  };

  const openEditModal = (scenario) => {
    setEditingId(scenario.id);
    setFormData({
      title: scenario.title,
      description: scenario.description,
      learning_objectives: scenario.learning_objectives,
      ai_system_prompt: scenario.ai_system_prompt,
      category: scenario.category,
      difficulty: scenario.difficulty
    });
    setIsModalOpen(true);
  };

  const resetForm = () => {
    setEditingId(null);
    setFormData({
      title: "",
      description: "",
      learning_objectives: "",
      ai_system_prompt: "",
      category: "Travel",
      difficulty: "medium"
    });
  };

  return (
    <div className="min-h-[100dvh] bg-zinc-50 flex flex-col">
      <TopBar />
      <div className="flex flex-1 pt-16">
        <Sidebar />
        
        <main className="flex-1 lg:ml-64 p-6 md:p-10 mb-24 lg:mb-0 overflow-y-auto w-full">
          <div className="max-w-6xl mx-auto w-full">
            <header className="mb-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div>
                <h1 className="text-4xl font-black tracking-tight text-zinc-950 font-display">Manage Scenarios</h1>
                <p className="text-zinc-500 font-medium">Add, update, or remove practice topics.</p>
              </div>
              <button 
                onClick={() => { resetForm(); setIsModalOpen(true); }}
                className="bg-primary text-white px-6 py-2.5 rounded-xl font-bold hover:scale-105 transition-all shadow-sm"
              >
                + New Scenario
              </button>
            </header>

            {isLoading ? (
              <div className="flex justify-center p-20"><div className="animate-spin h-8 w-8 border-b-2 border-primary rounded-full"></div></div>
            ) : (
              <div className="bg-white rounded-2xl shadow-sm border border-zinc-200 overflow-hidden w-full">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-zinc-50 text-xs uppercase tracking-wider text-zinc-500 border-b border-zinc-200">
                      <th className="p-4 font-bold">Title</th>
                      <th className="p-4 font-bold">Category</th>
                      <th className="p-4 font-bold">Difficulty</th>
                      <th className="p-4 font-bold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-100">
                    {scenarios.map(scen => (
                      <tr key={scen.id} className="hover:bg-zinc-50 transition-colors">
                        <td className="p-4">
                          <p className="font-bold text-zinc-900">{scen.title}</p>
                          <p className="text-xs text-zinc-500 line-clamp-1 max-w-sm">{scen.description}</p>
                        </td>
                        <td className="p-4 text-sm text-zinc-600 font-medium">
                          <span className="bg-zinc-100 px-3 py-1 rounded-full">{scen.category}</span>
                        </td>
                        <td className="p-4 text-sm text-zinc-600 font-medium capitalize">{scen.difficulty}</td>
                        <td className="p-4 text-right space-x-3">
                          <button onClick={() => openEditModal(scen)} className="text-primary hover:underline font-bold text-sm">Edit</button>
                          <button onClick={() => handleDelete(scen.id)} className="text-rose-500 hover:underline font-bold text-sm">Delete</button>
                        </td>
                      </tr>
                    ))}
                    {scenarios.length === 0 && (
                      <tr><td colSpan="4" className="p-8 text-center text-zinc-500">No scenarios found.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </main>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-8 shadow-2xl">
            <h2 className="text-2xl font-black mb-6">{editingId ? "Edit Scenario" : "Create Scenario"}</h2>
            
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase text-zinc-500 tracking-widest block ml-1">Title</label>
                <input required name="title" value={formData.title} onChange={handleChange} className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3 font-medium text-sm focus:ring-2 focus:ring-primary/20 outline-none" />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase text-zinc-500 tracking-widest block ml-1">Category</label>
                  <select name="category" value={formData.category} onChange={handleChange} className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3 font-medium text-sm outline-none">
                    <option value="Travel">Travel</option>
                    <option value="Business">Business</option>
                    <option value="Daily Life">Daily Life</option>
                    <option value="Sci-Tech">Sci-Tech</option>
                    <option value="Social">Social</option>
                    <option value="Hobbies">Hobbies</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase text-zinc-500 tracking-widest block ml-1">Difficulty</label>
                  <select name="difficulty" value={formData.difficulty} onChange={handleChange} className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3 font-medium text-sm outline-none">
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase text-zinc-500 tracking-widest block ml-1">Description</label>
                <textarea required name="description" value={formData.description} onChange={handleChange} rows={2} className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3 font-medium text-sm focus:ring-2 focus:ring-primary/20 outline-none resize-none" />
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase text-zinc-500 tracking-widest block ml-1">Learning Objectives</label>
                <textarea name="learning_objectives" value={formData.learning_objectives} onChange={handleChange} rows={2} className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3 font-medium text-sm focus:ring-2 focus:ring-primary/20 outline-none resize-none" />
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase text-zinc-500 tracking-widest block ml-1">AI System Prompt</label>
                <textarea required name="ai_system_prompt" value={formData.ai_system_prompt} onChange={handleChange} rows={4} className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3 font-medium text-sm focus:ring-2 focus:ring-primary/20 outline-none resize-none font-mono" placeholder="You are a helpful assistant..." />
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button type="button" onClick={() => setIsModalOpen(false)} className="px-6 py-3 font-bold text-zinc-500 hover:bg-zinc-100 rounded-xl transition-colors">Cancel</button>
                <button type="submit" className="px-8 py-3 bg-primary text-white font-bold rounded-xl shadow-lg shadow-primary/20 hover:scale-105 active:scale-95 transition-all">Save Scenario</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminScenarios;
