import { useMemo, useState } from "react";
import { ArrowCounterClockwise, FloppyDisk, GlobeHemisphereWest, ImageSquare, LinkSimple } from "@phosphor-icons/react";

import AdminShell from "@/features/admin-scenarios/components/AdminShell";
import SiteFooter from "@/shared/components/SiteFooter";
import { defaultSiteSettings, getSiteSettings, saveSiteSettings } from "@/shared/config/siteSettings";

const fieldClass = "w-full rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-sm font-semibold text-zinc-800 outline-none transition focus:border-brand-blue focus:ring-4 focus:ring-brand-blue/10 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100";

const socialFields = [
  { key: "facebook", label: "Facebook URL", placeholder: "https://facebook.com/..." },
  { key: "community", label: "Community URL", placeholder: "https://facebook.com/groups/..." },
  { key: "tiktok", label: "TikTok URL", placeholder: "https://tiktok.com/@..." },
  { key: "email", label: "Email link", placeholder: "mailto:hello@example.com" },
];

const AdminSiteSettingsPage = () => {
  const [settings, setSettings] = useState(getSiteSettings);
  const [savedMessage, setSavedMessage] = useState("");

  const previewSettings = useMemo(
    () => ({
      ...defaultSiteSettings,
      ...settings,
      socialLinks: {
        ...defaultSiteSettings.socialLinks,
        ...(settings.socialLinks || {}),
      },
    }),
    [settings],
  );

  const updateField = (key, value) => {
    setSavedMessage("");
    setSettings((current) => ({ ...current, [key]: value }));
  };

  const updateSocialField = (key, value) => {
    setSavedMessage("");
    setSettings((current) => ({
      ...current,
      socialLinks: {
        ...current.socialLinks,
        [key]: value,
      },
    }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const saved = saveSiteSettings(previewSettings);
    setSettings(saved);
    setSavedMessage("Đã lưu cấu hình giao diện.");
  };

  const resetDefaults = () => {
    const saved = saveSiteSettings(defaultSiteSettings);
    setSettings(saved);
    setSavedMessage("Đã khôi phục cấu hình mặc định.");
  };

  return (
    <AdminShell title="Site Settings" subtitle="Chỉnh logo, tên thương hiệu, footer và mạng xã hội landing page.">
      <form onSubmit={handleSubmit} className="space-y-8 p-4 md:p-8">
        <section className="grid gap-6 lg:grid-cols-[0.92fr_1.08fr]">
          <div className="rounded-[28px] border border-border bg-card p-6 shadow-sm">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-2xl bg-brand-blue/10 text-brand-blue">
                <ImageSquare size={24} weight="duotone" />
              </div>
              <div>
                <h2 className="text-xl font-black">Thương hiệu</h2>
                <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">Logo và text hiển thị ở navbar/footer.</p>
              </div>
            </div>

            <div className="space-y-4">
              <label className="block">
                <span className="mb-2 block text-sm font-bold text-zinc-600 dark:text-zinc-300">Tên thương hiệu</span>
                <input className={fieldClass} value={settings.brandName} onChange={(event) => updateField("brandName", event.target.value)} />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-bold text-zinc-600 dark:text-zinc-300">Tagline</span>
                <input className={fieldClass} value={settings.tagline} onChange={(event) => updateField("tagline", event.target.value)} />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-bold text-zinc-600 dark:text-zinc-300">Logo URL</span>
                <input className={fieldClass} value={settings.logoUrl} onChange={(event) => updateField("logoUrl", event.target.value)} placeholder="https://... hoặc /assets/..." />
              </label>
            </div>
          </div>

          <div className="rounded-[28px] border border-border bg-card p-6 shadow-sm">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-2xl bg-brand-green/10 text-brand-green-dark">
                <LinkSimple size={24} weight="duotone" />
              </div>
              <div>
                <h2 className="text-xl font-black">Mạng xã hội</h2>
                <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">Điền link thật để footer mở đúng kênh.</p>
              </div>
            </div>

            <div className="space-y-4">
              {socialFields.map((field) => (
                <label key={field.key} className="block">
                  <span className="mb-2 block text-sm font-bold text-zinc-600 dark:text-zinc-300">{field.label}</span>
                  <input
                    className={fieldClass}
                    value={settings.socialLinks?.[field.key] || ""}
                    onChange={(event) => updateSocialField(field.key, event.target.value)}
                    placeholder={field.placeholder}
                  />
                </label>
              ))}
              <label className="block">
                <span className="mb-2 block text-sm font-bold text-zinc-600 dark:text-zinc-300">Ghi chú liên hệ</span>
                <textarea className={`${fieldClass} min-h-24 resize-y`} value={settings.contactNote} onChange={(event) => updateField("contactNote", event.target.value)} />
              </label>
            </div>
          </div>
        </section>

        <div className="flex flex-col gap-3 rounded-[28px] border border-border bg-card p-5 shadow-sm md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3 text-sm font-semibold text-zinc-500 dark:text-zinc-400">
            <GlobeHemisphereWest size={22} weight="duotone" />
            Cấu hình lưu ở trình duyệt hiện tại và cập nhật ngay landing/footer.
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <button type="button" onClick={resetDefaults} className="inline-flex items-center justify-center gap-2 rounded-2xl border border-zinc-200 px-5 py-3 text-sm font-black text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800">
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
            <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">Bấm lưu để preview dùng cấu hình mới.</p>
          </div>
          <SiteFooter className="bg-transparent p-0 md:p-0" />
        </section>
      </form>
    </AdminShell>
  );
};

export default AdminSiteSettingsPage;
