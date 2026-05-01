import { useCallback, useEffect, useState } from "react";
import { Gift, X } from "@phosphor-icons/react";
import { gamificationApi } from "@/features/gamification/api/gamificationApi";

const EMPTY_FORM = {
  recipient_name: "",
  phone: "",
  address: "",
  note: "",
};

const ShopPage = () => {
  const [dashboard, setDashboard] = useState(null);
  const [items, setItems] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isRedeeming, setIsRedeeming] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      const [dashboardData, shopData] = await Promise.all([
        gamificationApi.getDashboard(),
        gamificationApi.getShop(),
      ]);
      setDashboard(dashboardData);
      setItems(shopData.items || []);
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể tải cửa hàng.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const openRedeemForm = (item) => {
    setSelectedItem(item);
    setForm(EMPTY_FORM);
    setError("");
    setNotice("");
  };

  const closeRedeemForm = () => {
    if (isRedeeming) return;
    setSelectedItem(null);
    setForm(EMPTY_FORM);
  };

  const updateForm = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const redeem = async (event) => {
    event.preventDefault();
    if (!selectedItem) return;
    setIsRedeeming(true);
    setError("");
    setNotice("");
    try {
      const response = await gamificationApi.redeemShopProduct({
        product_code: selectedItem.code,
        recipient_name: form.recipient_name.trim(),
        phone: form.phone.trim(),
        address: form.address.trim(),
        note: form.note.trim() || null,
      });
      setDashboard(response.dashboard);
      setNotice(`Đã gửi yêu cầu đổi quà: ${response.item.name}.`);
      setSelectedItem(null);
      setForm(EMPTY_FORM);
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể đổi sản phẩm.");
    } finally {
      setIsRedeeming(false);
    }
  };

  const coinBalance = Number(dashboard?.coin?.balance || 0);

  if (isLoading) {
    return <div className="p-8 text-sm font-semibold text-muted-foreground">Đang tải cửa hàng...</div>;
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.2em] text-primary">Shop</p>
          <h1 className="mt-1 text-3xl font-black text-zinc-950">Đổi Coin lấy quà</h1>
          <p className="mt-2 text-sm text-muted-foreground">Chọn sản phẩm vật lý và nhập địa chỉ nhận hàng.</p>
        </div>
        <div className="rounded-xl border border-border bg-card px-4 py-3 text-sm font-black text-zinc-800">
          {coinBalance.toLocaleString("en-US")} Coin
        </div>
      </div>

      {(notice || error) && (
        <div className={`mb-5 rounded-xl px-4 py-3 text-sm font-semibold ${error ? "bg-rose-50 text-rose-700" : "bg-emerald-50 text-emerald-700"}`}>
          {error || notice}
        </div>
      )}

      {items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-border bg-card p-8 text-center text-sm font-semibold text-muted-foreground">
          Hiện chưa có sản phẩm có thể đổi.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {items.map((item) => {
            const disabled = isRedeeming || coinBalance < item.price_coin || item.stock_quantity <= 0;
            return (
              <article key={item.code} className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
                <div className="flex h-44 items-center justify-center bg-zinc-100 text-zinc-400">
                  {item.image_url ? (
                    <img src={item.image_url} alt={item.name} className="h-full w-full object-cover" />
                  ) : (
                    <Gift size={48} weight="duotone" />
                  )}
                </div>
                <div className="p-5">
                  <div className="flex items-start justify-between gap-4">
                    <h2 className="text-xl font-black text-zinc-950">{item.name}</h2>
                    <span className="shrink-0 rounded-full bg-amber-50 px-3 py-1 text-xs font-black text-amber-700">
                      {item.price_coin} Coin
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.description}</p>
                  <p className="mt-3 text-xs font-black uppercase tracking-[0.16em] text-zinc-400">
                    Còn {item.stock_quantity} sản phẩm
                  </p>
                  <button
                    type="button"
                    disabled={disabled}
                    onClick={() => openRedeemForm(item)}
                    className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-zinc-950 px-4 py-3 text-sm font-black text-white disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    <Gift size={16} weight="fill" />
                    Đổi ngay
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 py-6">
          <form onSubmit={redeem} className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
            <div className="mb-5 flex items-start justify-between gap-4">
              <div>
                <p className="text-[11px] font-black uppercase tracking-[0.2em] text-primary">Thông tin nhận hàng</p>
                <h2 className="mt-1 text-2xl font-black text-zinc-950">{selectedItem.name}</h2>
              </div>
              <button type="button" onClick={closeRedeemForm} className="rounded-full p-2 text-zinc-500 hover:bg-zinc-100">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              <label className="block text-sm font-bold text-zinc-700">
                Họ tên
                <input required value={form.recipient_name} onChange={(event) => updateForm("recipient_name", event.target.value)} className="mt-2 w-full rounded-xl border border-border px-4 py-3 text-sm outline-none focus:border-primary" />
              </label>
              <label className="block text-sm font-bold text-zinc-700">
                SĐT
                <input required value={form.phone} onChange={(event) => updateForm("phone", event.target.value)} className="mt-2 w-full rounded-xl border border-border px-4 py-3 text-sm outline-none focus:border-primary" />
              </label>
              <label className="block text-sm font-bold text-zinc-700">
                Địa chỉ đầy đủ
                <textarea required rows={3} value={form.address} onChange={(event) => updateForm("address", event.target.value)} className="mt-2 w-full rounded-xl border border-border px-4 py-3 text-sm outline-none focus:border-primary" />
              </label>
              <label className="block text-sm font-bold text-zinc-700">
                Ghi chú
                <textarea rows={2} value={form.note} onChange={(event) => updateForm("note", event.target.value)} className="mt-2 w-full rounded-xl border border-border px-4 py-3 text-sm outline-none focus:border-primary" />
              </label>
            </div>

            <button type="submit" disabled={isRedeeming} className="mt-6 w-full rounded-xl bg-primary px-4 py-3 text-sm font-black text-white disabled:opacity-50">
              {isRedeeming ? "Đang gửi..." : `Xác nhận đổi ${selectedItem.price_coin} Coin`}
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

export default ShopPage;
