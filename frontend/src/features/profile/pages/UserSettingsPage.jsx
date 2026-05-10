import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CaretLeft, Camera, SignOut } from "@phosphor-icons/react";
import { useAuth } from "@/features/auth/context/AuthContext";

const toNullableString = (value) => {
  const trimmed = String(value || "").trim();
  return trimmed || null;
};

const UserSettingsPage = () => {
  const { user, updateProfileWithAvatar, changePassword, logout } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    display_name: user?.display_name || "",
    avatar: user?.avatar || "",
    age: user?.age || "",
    level: user?.level || "beginner",
  });

  const [passwordData, setPasswordData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });

  const [isSaving, setIsSaving] = useState(false);
  const [avatarFile, setAvatarFile] = useState(null);
  const [avatarPreviewUrl, setAvatarPreviewUrl] = useState("");
  const [message, setMessage] = useState({ type: "", text: "" });

  useEffect(() => {
    if (user) {
      if (avatarPreviewUrl) URL.revokeObjectURL(avatarPreviewUrl);
      setAvatarFile(null);
      setAvatarPreviewUrl("");
      setFormData({
        display_name: user.display_name || "",
        avatar: user.avatar || "",
        age: user.age || "",
        level: user.level || "beginner",
      });
    }
  }, [user]);

  useEffect(() => () => {
    if (avatarPreviewUrl) URL.revokeObjectURL(avatarPreviewUrl);
  }, [avatarPreviewUrl]);

  const handleProfileUpdate = async (event) => {
    event.preventDefault();
    setIsSaving(true);
    setMessage({ type: "", text: "" });

    try {
      await updateProfileWithAvatar({
        display_name: toNullableString(formData.display_name),
        avatar: toNullableString(formData.avatar),
        age: formData.age === "" ? null : Number(formData.age),
        level: toNullableString(formData.level),
      }, avatarFile);
      if (avatarPreviewUrl) URL.revokeObjectURL(avatarPreviewUrl);
      setAvatarFile(null);
      setAvatarPreviewUrl("");
      setMessage({ type: "success", text: "Đã cập nhật hồ sơ." });
    } catch {
      setMessage({ type: "error", text: "Không thể cập nhật hồ sơ. Vui lòng thử lại." });
    } finally {
      setIsSaving(false);
    }
  };

  const handleAvatarSelect = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setMessage({ type: "", text: "" });
    if (avatarPreviewUrl) {
      URL.revokeObjectURL(avatarPreviewUrl);
    }
    setAvatarFile(file);
    setAvatarPreviewUrl(URL.createObjectURL(file));
    setMessage({ type: "success", text: "Đã chọn avatar. Ảnh sẽ upload khi lưu hồ sơ." });
    event.target.value = "";
  };

  const handlePasswordChange = async (event) => {
    event.preventDefault();
    if (!user?.has_password) {
      navigate(`/reset-password?email=${encodeURIComponent(user?.email || "")}`);
      return;
    }
    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage({ type: "error", text: "Mật khẩu mới không khớp." });
      return;
    }

    setIsSaving(true);
    setMessage({ type: "", text: "" });

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
    <div className="app-page-narrow max-w-3xl">
      <div className="mb-8 flex items-center justify-between border-b-2 border-[#e5e5e5] pb-6">
        <div className="flex items-center gap-4">
          <Link to="/profile" className="rounded-xl p-2 text-[#afafaf] transition-colors hover:bg-[#f7f7f7]">
            <CaretLeft size={24} weight="bold" />
          </Link>
          <div>
            <p className="text-xs font-black uppercase tracking-wide text-[#afafaf]">Cài đặt tài khoản</p>
            <h1 className="text-2xl font-black text-[#4b4b4b]">Hồ sơ & mật khẩu</h1>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-3 py-2 text-sm font-black uppercase text-[#ff4b4b] hover:brightness-90"
        >
          <SignOut size={20} weight="bold" />
          Đăng xuất
        </button>
      </div>

      {message.text && (
        <div className={`mb-6 rounded-2xl border-2 p-4 font-bold ${message.type === "success" ? "border-[#84d8ff] bg-[#ddf4ff] text-[#1cb0f6]" : "border-[#ff4b4b]/20 bg-[#fff0f0] text-[#ff4b4b]"}`}>
          {message.text}
        </div>
      )}

      <div className="space-y-6">
        <section className="rounded-2xl border-2 border-[#e5e5e5] bg-white p-6 shadow-sm">
          <div className="mb-6">
            <h2 className="text-xl font-black text-[#4b4b4b]">Chỉnh sửa hồ sơ</h2>
            <p className="mt-1 text-sm font-bold text-[#afafaf]">Thông tin hiển thị trong tài khoản học viên.</p>
          </div>

          <form onSubmit={handleProfileUpdate} className="space-y-6">
            <div className="flex flex-col gap-6 sm:flex-row sm:items-end">
              <div className="relative shrink-0">
                <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-full border-2 border-[#e5e5e5] bg-[#4B4B4B]">
                  {avatarPreviewUrl || formData.avatar ? (
                    <img src={avatarPreviewUrl || formData.avatar} alt="Avatar" className="h-full w-full object-cover" />
                  ) : (
                    <span className="text-2xl font-black text-white">{formData.display_name.slice(0, 1).toUpperCase()}</span>
                  )}
                </div>
                <label className="absolute bottom-0 right-0 flex h-8 w-8 cursor-pointer items-center justify-center rounded-full border-2 border-[#e5e5e5] bg-white text-[#1cb0f6] shadow-sm transition hover:scale-105">
                  <Camera size={16} weight="bold" />
                  <input type="file" accept="image/*" onChange={handleAvatarSelect} className="hidden" />
                </label>
              </div>

              <div className="flex-1">
                <div>
                  <label className="app-label">Tên hiển thị</label>
                  <input
                    type="text"
                    className="app-input"
                    value={formData.display_name}
                    onChange={(event) => setFormData({ ...formData, display_name: event.target.value })}
                  />
                </div>
                <p className="mt-3 text-xs font-bold text-[#afafaf]">
                  {avatarFile ? "Avatar đã chọn, sẽ upload khi lưu hồ sơ." : "Bấm biểu tượng camera để chọn avatar."}
                </p>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="app-label">Tuổi</label>
                <input
                  type="number"
                  min="1"
                  max="120"
                  className="app-input"
                  value={formData.age}
                  onChange={(event) => setFormData({ ...formData, age: event.target.value })}
                />
              </div>
              <div>
                <label className="app-label">Trình độ</label>
                <select
                  className="app-input"
                  value={formData.level}
                  onChange={(event) => setFormData({ ...formData, level: event.target.value })}
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
            </div>

            <button type="submit" disabled={isSaving} className="app-button-primary w-full sm:w-auto px-12">
              {isSaving ? "Đang lưu..." : "Lưu hồ sơ"}
            </button>
          </form>
        </section>

        <section className="rounded-2xl border-2 border-[#e5e5e5] bg-white p-6 shadow-sm">
          <div className="mb-6">
            <h2 className="text-xl font-black text-[#4b4b4b]">Mật khẩu</h2>
            <p className="mt-1 text-sm font-bold text-[#afafaf]">Đổi mật khẩu hoặc đặt mật khẩu bằng OTP.</p>
          </div>

          {!user?.has_password ? (
            <div className="rounded-2xl border-2 border-[#84d8ff] bg-[#ddf4ff] p-5 text-sm font-bold text-[#1cb0f6]">
              Tài khoản này chưa có mật khẩu. Dùng OTP qua email để đặt mật khẩu an toàn.
              <button
                type="button"
                onClick={() => navigate(`/reset-password?email=${encodeURIComponent(user?.email || "")}`)}
                className="mt-4 block rounded-xl bg-[#1cb0f6] px-5 py-3 font-black text-white"
              >
                Đặt mật khẩu bằng OTP
              </button>
            </div>
          ) : (
            <form onSubmit={handlePasswordChange} className="space-y-6">
              <div>
                <label className="app-label">Mật khẩu hiện tại</label>
                <input
                  type="password"
                  className="app-input"
                  value={passwordData.current_password}
                  onChange={(event) => setPasswordData({ ...passwordData, current_password: event.target.value })}
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="app-label">Mật khẩu mới</label>
                  <input
                    type="password"
                    className="app-input"
                    value={passwordData.new_password}
                    onChange={(event) => setPasswordData({ ...passwordData, new_password: event.target.value })}
                  />
                </div>
                <div>
                  <label className="app-label">Nhập lại mật khẩu mới</label>
                  <input
                    type="password"
                    className="app-input"
                    value={passwordData.confirm_password}
                    onChange={(event) => setPasswordData({ ...passwordData, confirm_password: event.target.value })}
                  />
                </div>
              </div>

              <button type="submit" disabled={isSaving} className="app-button-secondary w-full sm:w-auto">
                Đổi mật khẩu
              </button>
            </form>
          )}
        </section>
      </div>
    </div>
  );
};

export default UserSettingsPage;
