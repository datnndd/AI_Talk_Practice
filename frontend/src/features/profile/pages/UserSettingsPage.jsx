import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CaretLeft, Camera, ShieldCheck, User as UserIcon, SignOut, Trash } from "@phosphor-icons/react";
import { useAuth } from "@/features/auth/context/AuthContext";

const UserSettingsPage = () => {
  const { user, updateProfile, changePassword, logout } = useAuth();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    display_name: user?.display_name || "",
    avatar: user?.avatar || "",
    handle: user?.preferences?.handle || "",
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
      });
    }
  }, [user]);

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setMessage({ type: "", text: "" });
    try {
      await updateProfile(formData);
      setMessage({ type: "success", text: "Profile updated successfully!" });
    } catch (err) {
      setMessage({ type: "error", text: "Failed to update profile. Please try again." });
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
      setMessage({ type: "success", text: "Password changed successfully!" });
      setPasswordData({ current_password: "", new_password: "", confirm_password: "" });
    } catch (err) {
      setMessage({ type: "error", text: "Failed to change password. check your current password." });
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
          <h1 className="text-2xl font-black text-[#4b4b4b]">Settings</h1>
        </div>
        <button 
          onClick={handleLogout}
          className="flex items-center gap-2 text-sm font-black uppercase text-[#ff4b4b] hover:brightness-90 px-4 py-2"
        >
          <SignOut size={20} weight="bold" />
          Logout
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
            Account
          </button>
          <button className="flex w-full items-center gap-4 rounded-xl border-2 border-transparent p-4 text-left font-black uppercase text-[#afafaf] transition-all hover:bg-[#f7f7f7]">
            <ShieldCheck size={24} weight="bold" />
            Privacy
          </button>
        </div>

        {/* Right Col: Forms */}
        <div className="lg:col-span-2 space-y-12">
          {/* Account Form */}
          <section className="space-y-6">
            <h2 className="text-xl font-black text-[#4b4b4b]">Account Information</h2>
            
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
                    <label className="duo-label">Display Name</label>
                    <input 
                      type="text" 
                      className="duo-input" 
                      value={formData.display_name}
                      onChange={(e) => setFormData({...formData, display_name: e.target.value})}
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className="duo-label">Username (Handle)</label>
                <input 
                  type="text" 
                  className="duo-input" 
                  value={formData.handle}
                  onChange={(e) => setFormData({...formData, handle: e.target.value})}
                  placeholder="learner123"
                />
                <p className="mt-2 text-xs font-bold text-[#afafaf]">This is your unique handle used for leaderboards and friends.</p>
              </div>

              <div className="pt-4">
                <button 
                  type="submit" 
                  disabled={isSaving}
                  className="duo-button-blue w-full sm:w-auto px-12"
                >
                  {isSaving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </section>

          {/* Password Form */}
          <section className="space-y-6 pt-12 border-t-2 border-[#e5e5e5]">
            <h2 className="text-xl font-black text-[#4b4b4b]">Security</h2>
            
            <form onSubmit={handlePasswordChange} className="space-y-6">
              <div>
                <label className="duo-label">Current Password</label>
                <input 
                  type="password" 
                  className="duo-input" 
                  value={passwordData.current_password}
                  onChange={(e) => setPasswordData({...passwordData, current_password: e.target.value})}
                />
              </div>
              <div>
                <label className="duo-label">New Password</label>
                <input 
                  type="password" 
                  className="duo-input" 
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({...passwordData, new_password: e.target.value})}
                />
              </div>
              <div>
                <label className="duo-label">Confirm New Password</label>
                <input 
                  type="password" 
                  className="duo-input" 
                  value={passwordData.confirm_password}
                  onChange={(e) => setPasswordData({...passwordData, confirm_password: e.target.value})}
                />
              </div>

              <div className="pt-4">
                <button 
                  type="submit" 
                  disabled={isSaving}
                  className="duo-button-secondary w-full sm:w-auto"
                >
                  Change Password
                </button>
              </div>
            </form>
          </section>

          {/* Danger Zone */}
          <section className="space-y-6 pt-12 border-t-2 border-[#e5e5e5]">
             <h2 className="text-xl font-black text-[#ff4b4b]">Danger Zone</h2>
             <p className="text-sm font-bold text-[#afafaf]">Once you delete your account, there is no going back. Please be certain.</p>
             <button className="flex items-center gap-2 rounded-xl border-2 border-b-4 border-[#ff4b4b]/20 bg-white px-6 py-3 font-black uppercase tracking-wide text-[#ff4b4b] hover:bg-[#fff0f0] active:border-b-2 active:translate-y-[2px] transition-all">
                <Trash size={20} weight="bold" />
                Delete Account
             </button>
          </section>
        </div>
      </div>
    </div>
  );
};

export default UserSettingsPage;
