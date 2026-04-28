import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CaretLeft, Camera, ShieldCheck, User as UserIcon, SignOut, Trash } from "@phosphor-icons/react";
import { useAuth } from "@/features/auth/context/AuthContext";

const toCommaText = (value) => {
  if (!value) return "";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
};

const toNullableString = (value) => {
  const trimmed = String(value || "").trim();
  return trimmed || null;
};

const UserSettingsPage = () => {
  const { user, updateProfile, changePassword, logout } = useAuth();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    display_name: user?.display_name || "",
    avatar: user?.avatar || "",
    handle: user?.preferences?.handle || "",
    age: user?.age || "",
    level: user?.level || "beginner",
    daily_goal: user?.daily_goal || 15,
    learning_purpose: toCommaText(user?.learning_purpose),
    favorite_topics: toCommaText(user?.favorite_topics),
    main_challenge: user?.main_challenge || "",
  });

  const [passwordData, setPasswordData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });

  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });

  useEffect(() => {
    if (user) {
      setFormData({
        display_name: user.display_name || "",
        avatar: user.avatar || "",
        handle: user.preferences?.handle || "",
        age: user.age || "",
        level: user.level || "beginner",
        daily_goal: user.daily_goal || 15,
        learning_purpose: toCommaText(user.learning_purpose),
        favorite_topics: toCommaText(user.favorite_topics),
        main_challenge: user.main_challenge || "",
      });
    }
  }, [user]);

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setMessage({ type: "", text: "" });
    try {
      await updateProfile({
        display_name: toNullableString(formData.display_name),
        avatar: toNullableString(formData.avatar),
        age: formData.age === "" ? null : Number(formData.age),
        level: toNullableString(formData.level),
        daily_goal: formData.daily_goal === "" ? null : Number(formData.daily_goal),
        learning_purpose: toNullableString(formData.learning_purpose),
        favorite_topics: toNullableString(formData.favorite_topics),
        main_challenge: toNullableString(formData.main_challenge),
        preferences: {
          ...(user?.preferences || {}),
          handle: toNullableString(formData.handle),
        },
      });
      setMessage({ type: "success", text: "Đã cập nhật hồ sơ." });
    } catch {
      setMessage({ type: "error", text: "Không thể cập nhật hồ sơ. Vui lòng thử lại." });
    } finally {
      setIsSaving(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage({ type: "error", text: "New passwords do not match." });
      return;
    }
    setIsSaving(true);
    try {
      await changePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });
      setMessage({ type: "success", text: "Đã đổi mật khẩu." });
      setPasswordData({ current_password: "", new_password: "", confirm_password: "" });
    } catch {
      setMessage({ type: "error", text: "Không thể đổi mật khẩu. Kiểm tra lại mật khẩu hiện tại." });
    } finally {
      setIsSaving(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8 pb-6 border-b-2 border-[#e5e5e5]">
        <div className="flex items-center gap-4">
          <Link to="/profile" className="p-2 rounded-xl hover:bg-[#f7f7f7] text-[#afafaf] transition-colors">
            <CaretLeft size={24} weight="bold" />
          </Link>
          <h1 className="text-2xl font-black text-[#4b4b4b]">Cài đặt hồ sơ</h1>
        </div>
        <button 
          onClick={handleLogout}
          className="flex items-center gap-2 text-sm font-black uppercase text-[#ff4b4b] hover:brightness-90 px-4 py-2"
        >
          <SignOut size={20} weight="bold" />
          Đăng xuất
        </button>
      </div>

      {message.text && (
        <div className={`mb-8 p-4 rounded-2xl border-2 font-bold ${message.type === 'success' ? 'bg-[#ddf4ff] border-[#84d8ff] text-[#1cb0f6]' : 'bg-[#fff0f0] border-[#ff4b4b]/20 text-[#ff4b4b]'}`}>
          {message.text}
        </div>
      )}

      <div className="grid gap-12 lg:grid-cols-3">
        {/* Left Col: Menu */}
        <div className="lg:col-span-1 space-y-2">
          <button className="flex w-full items-center gap-4 rounded-xl border-2 border-b-4 border-[#84d8ff] bg-[#ddf4ff] p-4 text-left font-black uppercase text-[#1cb0f6] transition-all">
            <UserIcon size={24} weight="bold" />
            Tài khoản
          </button>
          <button className="flex w-full items-center gap-4 rounded-xl border-2 border-transparent p-4 text-left font-black uppercase text-[#afafaf] transition-all hover:bg-[#f7f7f7]">
            <ShieldCheck size={24} weight="bold" />
            Quyền riêng tư
          </button>
        </div>

        {/* Right Col: Forms */}
        <div className="lg:col-span-2 space-y-12">
          {/* Account Form */}
          <section className="space-y-6">
            <h2 className="text-xl font-black text-[#4b4b4b]">Thông tin tài khoản</h2>
            
            <form onSubmit={handleProfileUpdate} className="space-y-6">
              <div className="flex flex-col gap-6 sm:flex-row sm:items-end">
                <div className="relative group shrink-0">
                  <div className="h-24 w-24 rounded-full border-2 border-[#e5e5e5] bg-[#4B4B4B] flex items-center justify-center overflow-hidden">
                    {formData.avatar ? (
                      <img src={formData.avatar} alt="Avatar" className="h-full w-full object-cover" />
                    ) : (
                      <span className="text-2xl font-black text-white">{formData.display_name.slice(0,1).toUpperCase()}</span>
                    )}
                  </div>
                  <button type="button" className="absolute bottom-0 right-0 h-8 w-8 rounded-full border-2 border-[#e5e5e5] bg-white flex items-center justify-center text-[#1cb0f6] shadow-sm transition-transform hover:scale-110">
                    <Camera size={16} weight="bold" />
                  </button>
                </div>
                <div className="flex-1 space-y-4">
                  <div>
                    <label className="app-label">Tên hiển thị</label>
                    <input 
                      type="text" 
                      className="app-input" 
                      value={formData.display_name}
                      onChange={(e) => setFormData({...formData, display_name: e.target.value})}
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className="app-label">Username (Handle)</label>
                <input 
                  type="text" 
                  className="app-input" 
                  value={formData.handle}
                  onChange={(e) => setFormData({...formData, handle: e.target.value})}
                  placeholder="learner123"
                />
                <p className="mt-2 text-xs font-bold text-[#afafaf]">Tên định danh được lưu trong preferences.handle.</p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="app-label">Avatar URL</label>
                  <input
                    type="url"
                    className="app-input"
                    value={formData.avatar}
                    onChange={(e) => setFormData({ ...formData, avatar: e.target.value })}
                    placeholder="https://..."
                  />
                </div>
                <div>
                  <label className="app-label">Tuổi</label>
                  <input
                    type="number"
                    min="1"
                    max="120"
                    className="app-input"
                    value={formData.age}
                    onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <label className="app-label">Trình độ</label>
                <select
                  className="app-input"
                  value={formData.level}
                  onChange={(e) => setFormData({ ...formData, level: e.target.value })}
                >
                  <option value="beginner">beginner</option>
                  <option value="intermediate">intermediate</option>
                  <option value="advanced">advanced</option>
                  <option value="A1">A1</option>
                  <option value="A2">A2</option>
                  <option value="B1">B1</option>
                  <option value="B2">B2</option>
                  <option value="C1">C1</option>
                  <option value="C2">C2</option>
                </select>
              </div>

              <div>
                <label className="app-label">Mục tiêu mỗi ngày (phút)</label>
                <input
                  type="number"
                  min="1"
                  max="1440"
                  className="app-input"
                  value={formData.daily_goal}
                  onChange={(e) => setFormData({ ...formData, daily_goal: e.target.value })}
                />
              </div>

              <div>
                <label className="app-label">Mục tiêu học</label>
                <input
                  type="text"
                  className="app-input"
                  value={formData.learning_purpose}
                  onChange={(e) => setFormData({ ...formData, learning_purpose: e.target.value })}
                  placeholder="Du lịch, công việc, phỏng vấn..."
                />
              </div>

              <div>
                <label className="app-label">Chủ đề yêu thích</label>
                <input
                  type="text"
                  className="app-input"
                  value={formData.favorite_topics}
                  onChange={(e) => setFormData({ ...formData, favorite_topics: e.target.value })}
                  placeholder="Travel, Business, Daily conversation"
                />
                <p className="mt-2 text-xs font-bold text-[#afafaf]">Ngăn cách nhiều chủ đề bằng dấu phẩy.</p>
              </div>

              <div>
                <label className="app-label">Thử thách chính</label>
                <textarea
                  className="app-input min-h-28"
                  value={formData.main_challenge}
                  onChange={(e) => setFormData({ ...formData, main_challenge: e.target.value })}
                  placeholder="Ví dụ: phát âm chưa tự nhiên, thiếu từ vựng..."
                />
              </div>

              <div className="pt-4">
                <button 
                  type="submit" 
                  disabled={isSaving}
                  className="app-button-primary w-full sm:w-auto px-12"
                >
                  {isSaving ? "Đang lưu..." : "Lưu thay đổi"}
                </button>
              </div>
            </form>
          </section>

          {/* Password Form */}
          <section className="space-y-6 pt-12 border-t-2 border-[#e5e5e5]">
            <h2 className="text-xl font-black text-[#4b4b4b]">Bảo mật</h2>
            
            <form onSubmit={handlePasswordChange} className="space-y-6">
              <div>
                <label className="app-label">Mật khẩu hiện tại</label>
                <input 
                  type="password" 
                  className="app-input" 
                  value={passwordData.current_password}
                  onChange={(e) => setPasswordData({...passwordData, current_password: e.target.value})}
                />
              </div>
              <div>
                <label className="app-label">Mật khẩu mới</label>
                <input 
                  type="password" 
                  className="app-input" 
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({...passwordData, new_password: e.target.value})}
                />
              </div>
              <div>
                <label className="app-label">Nhập lại mật khẩu mới</label>
                <input 
                  type="password" 
                  className="app-input" 
                  value={passwordData.confirm_password}
                  onChange={(e) => setPasswordData({...passwordData, confirm_password: e.target.value})}
                />
              </div>

              <div className="pt-4">
                <button 
                  type="submit" 
                  disabled={isSaving}
                  className="app-button-secondary w-full sm:w-auto"
                >
                  Đổi mật khẩu
                </button>
              </div>
            </form>
          </section>

          {/* Danger Zone */}
          <section className="space-y-6 pt-12 border-t-2 border-[#e5e5e5]">
             <h2 className="text-xl font-black text-[#ff4b4b]">Vùng nguy hiểm</h2>
             <p className="text-sm font-bold text-[#afafaf]">Sau khi xóa tài khoản, dữ liệu không thể khôi phục.</p>
             <button className="flex items-center gap-2 rounded-xl border-2 border-b-4 border-[#ff4b4b]/20 bg-white px-6 py-3 font-black uppercase tracking-wide text-[#ff4b4b] hover:bg-[#fff0f0] active:border-b-2 active:translate-y-[2px] transition-all">
                <Trash size={20} weight="bold" />
                Xóa tài khoản
             </button>
          </section>
        </div>
      </div>
    </div>
  );
};

export default UserSettingsPage;
