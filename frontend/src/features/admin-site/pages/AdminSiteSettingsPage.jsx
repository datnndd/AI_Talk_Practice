import { useMemo, useState } from "react";
import { ArrowCounterClockwise, FloppyDisk, GlobeHemisphereWest, ImageSquare, LinkSimple, UploadSimple } from "@phosphor-icons/react";

import AdminShell from "@/shared/components/admin/AdminShell";
import SiteFooter from "@/shared/components/SiteFooter";
import { adminSiteApi } from "@/features/admin-site/api/adminSiteApi";
import { defaultSiteSettings, getSiteSettings, normalizeSiteSettings, saveSiteSettings } from "@/shared/config/siteSettings";

const fieldClass = "w-full rounded-2xl border border-border bg-card px-4 py-3 text-sm font-semibold text-[var(--page-fg)] outline-none transition focus:border-brand-blue focus:ring-4 focus:ring-brand-blue/10   ";

const socialFields = [
  { key: "facebook", label: "Facebook URL", placeholder: "https://facebook.com/..." },
  { key: "community", label: "Community URL", placeholder: "https://facebook.com/groups/..." },
  { key: "tiktok", label: "TikTok URL", placeholder: "https://tiktok.com/@..." },
  { key: "email", label: "Email link", placeholder: "mailto:hello@example.com" },
];

const toSocialOnlySettings = (settings = {}) => normalizeSiteSettings({
  ...defaultSiteSettings,
  logoUrl: settings.logoUrl || defaultSiteSettings.logoUrl,
  contactNote: settings.contactNote ?? defaultSiteSettings.contactNote,
  socialLinks: settings.socialLinks || defaultSiteSettings.socialLinks,
});

const AdminSiteSettingsPage = () => {
  const [settings, setSettings] = useState(() => toSocialOnlySettings(getSiteSettings()));
  const [savedMessage, setSavedMessage] = useState("");
  const [uploadError, setUploadError] = useState("");
  const [isUploadingLogo, setIsUploadingLogo] = useState(false);

  const previewSettings = useMemo(() => normalizeSiteSettings(settings), [settings]);

  const updateField = (key, value) => {
    setSavedMessage("");
    setUploadError("");
    setSettings((current) => ({ ...current, [key]: value }));
  };

  const updateSocialField = (key, value) => {
    setSavedMessage("");
    setUploadError("");
    setSettings((current) => ({
      ...current,
      socialLinks: {
        ...current.socialLinks,
        [key]: value,
      },
    }));
  };

  const uploadLogo = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setSavedMessage("");
    setUploadError("");
    setIsUploadingLogo(true);
    try {
      const uploaded = await adminSiteApi.uploadLogo(file);
      setSettings((current) => ({ ...current, logoUrl: uploaded.url }));
      setSavedMessage("Đã upload logo. Bấm Lưu thay đổi để áp dụng.");
    } catch (error) {
      setUploadError(error?.response?.data?.detail || error?.message || "Không thể upload logo.");
    } finally {
      setIsUploadingLogo(false);
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const saved = saveSiteSettings(toSocialOnlySettings(previewSettings));
    setSettings(saved);
    setSavedMessage("Đã lưu cấu hình logo và mạng xã hội.");
  };

  const resetDefaults = () => {
    const saved = saveSiteSettings(toSocialOnlySettings(defaultSiteSettings));
    setSettings(saved);
    setSavedMessage("Đã khôi phục logo và mạng xã hội mặc định.");
  };

  return (
    <AdminShell title="Site Settings" subtitle="Chỉnh logo, link mạng xã hội và thông tin liên hệ ở footer.">
      <form onSubmit={handleSubmit} className="space-y-8 p-4 md:p-8">
        <section className="grid min-w-0 gap-6 lg:grid-cols-2">
          <div className="min-w-0 rounded-[28px] border border-border bg-card p-6 shadow-sm">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-2xl bg-brand-blue/10 text-brand-blue">
                <ImageSquare size={24} weight="duotone" />
              </div>
              <div>
                <h2 className="text-xl font-black">Logo</h2>
                <p className="text-sm font-medium text-[var(--page-muted)] ">Upload ảnh lên Supabase và dùng ở navbar/footer.</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="grid min-w-0 grid-cols-[64px_minmax(0,1fr)] items-center gap-4 rounded-2xl bg-muted p-4">
                <img src={previewSettings.logoUrl} alt="Logo preview" className="h-16 w-16 rounded-2xl object-cover shadow-sm" />
                <div className="min-w-0 overflow-hidden">
                  <p className="text-sm font-black">Logo hiện tại</p>
                  <p className="mt-1 max-w-full truncate text-xs font-semibold text-[var(--page-muted)]">{previewSettings.logoUrl}</p>
                </div>
              </div>
              <label className="block">
                <span className="mb-2 block text-sm font-bold text-[var(--page-muted)] ">Logo URL</span>
                <input className={fieldClass} value={settings.logoUrl} onChange={(event) => updateField("logoUrl", event.target.value)} placeholder="https://... hoặc /assets/..." />
              </label>
              <label className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-2xl bg-brand-blue px-5 py-3 text-sm font-black text-white shadow-[0_4px_0_0_#1899D6] active:translate-y-[3px] active:shadow-none">
                <UploadSimple size={18} weight="bold" />
                {isUploadingLogo ? "Đang upload..." : "Upload logo"}
                <input type="file" accept="image/*" onChange={uploadLogo} disabled={isUploadingLogo} className="hidden" />
              </label>
              {uploadError ? <p className="text-sm font-bold text-rose-600">{uploadError}</p> : null}
            </div>
          </div>

          <div className="min-w-0 rounded-[28px] border border-border bg-card p-6 shadow-sm">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-2xl bg-brand-green/10 text-brand-green-dark">
                <LinkSimple size={24} weight="duotone" />
              </div>
              <div>
                <h2 className="text-xl font-black">Mạng xã hội</h2>
                <p className="text-sm font-medium text-[var(--page-muted)] ">Điền link thật để footer mở đúng kênh.</p>
              </div>
            </div>

            <div className="space-y-4">
              {socialFields.map((field) => (
                <label key={field.key} className="block">
                  <span className="mb-2 block text-sm font-bold text-[var(--page-muted)] ">{field.label}</span>
                  <input
                    className={fieldClass}
                    value={settings.socialLinks?.[field.key] || ""}
                    onChange={(event) => updateSocialField(field.key, event.target.value)}
                    placeholder={field.placeholder}
                  />
                </label>
              ))}
              <label className="block">
                <span className="mb-2 block text-sm font-bold text-[var(--page-muted)] ">Ghi chú liên hệ</span>
                <textarea className={`${fieldClass} min-h-24 resize-y`} value={settings.contactNote} onChange={(event) => updateField("contactNote", event.target.value)} />
              </label>
            </div>
          </div>
        </section>

        <div className="flex flex-col gap-3 rounded-[28px] border border-border bg-card p-5 shadow-sm md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3 text-sm font-semibold text-[var(--page-muted)] ">
            <GlobeHemisphereWest size={22} weight="duotone" />
            Cấu hình logo/social lưu ở trình duyệt hiện tại và cập nhật ngay footer.
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <button type="button" onClick={resetDefaults} className="inline-flex items-center justify-center gap-2 rounded-2xl border border-border px-5 py-3 text-sm font-black text-[var(--page-muted)] hover:bg-muted">
              <ArrowCounterClockwise size={18} weight="bold" />
              Mặc định
            </button>
            <button type="submit" className="inline-flex items-center justify-center gap-2 rounded-2xl bg-brand-green px-5 py-3 text-sm font-black text-white shadow-[0_4px_0_0_#46a302] active:translate-y-[3px] active:shadow-none">
              <FloppyDisk size={18} weight="bold" />
              Lưu thay đổi
            </button>
          </div>
        </div>

        {savedMessage ? (
          <div className="rounded-2xl border border-brand-green/20 bg-brand-green/10 px-4 py-3 text-sm font-bold text-brand-green-dark">
            {savedMessage}
          </div>
        ) : null}

        <section className="rounded-[28px] border border-border bg-card p-4 shadow-sm">
          <div className="px-2 pb-3">
            <h2 className="text-xl font-black">Preview footer</h2>
            <p className="text-sm font-medium text-[var(--page-muted)] ">Preview cập nhật theo form hiện tại.</p>
          </div>
          <SiteFooter className="bg-transparent p-0 md:p-0" settings={previewSettings} />
        </section>
      </form>
    </AdminShell>
  );
};

export default AdminSiteSettingsPage;
