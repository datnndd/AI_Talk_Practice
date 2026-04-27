import { useCallback, useEffect, useState } from "react";
import { CrownSimple, Ticket } from "@phosphor-icons/react";
import { gamificationApi } from "@/features/gamification/api/gamificationApi";

const ShopPage = () => {
  const [dashboard, setDashboard] = useState(null);
  const [items, setItems] = useState([]);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isPurchasing, setIsPurchasing] = useState(false);

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

  const purchase = async (itemCode) => {
    setIsPurchasing(true);
    setError("");
    setNotice("");
    try {
      const response = await gamificationApi.purchaseShopItem(itemCode);
      setDashboard(response.dashboard);
      setNotice(`Đã mua ${response.item.name}. Pro được kích hoạt.`);
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể mua vật phẩm.");
    } finally {
      setIsPurchasing(false);
    }
  };

  if (isLoading) {
    return <div className="p-8 text-sm font-semibold text-muted-foreground">Đang tải cửa hàng...</div>;
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.2em] text-primary">Shop</p>
          <h1 className="mt-1 text-3xl font-black text-zinc-950">Cửa hàng Coin</h1>
        </div>
        <div className="rounded-xl border border-border bg-card px-4 py-3 text-sm font-black text-zinc-800">
          {Number(dashboard?.coin?.balance || 0).toLocaleString("en-US")} Coin
        </div>
      </div>

      {(notice || error) && (
        <div className={`mb-5 rounded-xl px-4 py-3 text-sm font-semibold ${error ? "bg-rose-50 text-rose-700" : "bg-emerald-50 text-emerald-700"}`}>
          {error || notice}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {items.map((item) => (
          <article key={item.code} className="rounded-xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-start justify-between gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Ticket size={24} weight="fill" />
              </div>
              <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-black text-amber-700">
                {item.price_coin} Coin
              </span>
            </div>
            <h2 className="mt-4 text-xl font-black text-zinc-950">{item.name}</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.description}</p>
            <button
              type="button"
              disabled={isPurchasing || Number(dashboard?.coin?.balance || 0) < item.price_coin}
              onClick={() => purchase(item.code)}
              className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-zinc-950 px-4 py-3 text-sm font-black text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              <CrownSimple size={16} weight="fill" />
              Mua ngay
            </button>
          </article>
        ))}
      </div>
    </div>
  );
};

export default ShopPage;
