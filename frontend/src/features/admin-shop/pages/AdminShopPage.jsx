import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CheckCircle, CreditCard, Gift, GraduationCap, PencilSimple, Plus, ProhibitInset, SquaresFour, Trash, UserList } from "@phosphor-icons/react";

import { adminShopApi } from "@/features/admin-shop/api/adminShopApi";
import AdminShell from "@/features/admin-scenarios/components/AdminShell";

const EMPTY_PRODUCT = {
  code: "",
  name: "",
  description: "",
  price_coin: 0,
  image_url: "",
  stock_quantity: 0,
  is_active: true,
  sort_order: 0,
};

const adminNavItems = [
  { label: "Users", icon: UserList, to: "/admin/users" },
  { label: "Scenario Library", icon: SquaresFour, to: "/admin/scenarios" },
  { label: "Curriculum", icon: GraduationCap, to: "/admin/curriculum" },
  { label: "Shop", icon: Gift, to: "/admin/shop" },
  { label: "Transactions", icon: CreditCard, to: "/admin/payments" },
];

const statuses = ["pending", "processing", "shipped", "completed", "cancelled"];

const formatDateTime = (value) => value ? new Date(value).toLocaleString("vi-VN") : "--";

const AdminShopPage = () => {
  const [tab, setTab] = useState("products");
  const [products, setProducts] = useState([]);
  const [redemptions, setRedemptions] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState(null);
  const [form, setForm] = useState(EMPTY_PRODUCT);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const imageInputRef = useRef(null);

  const selectedProduct = useMemo(
    () => products.find((product) => product.id === selectedProductId) || null,
    [products, selectedProductId],
  );

  const load = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      const [productData, redemptionData] = await Promise.all([
        adminShopApi.listProducts(),
        adminShopApi.listRedemptions(),
      ]);
      setProducts(productData || []);
      setRedemptions(redemptionData || []);
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể tải dữ liệu shop.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!selectedProduct) return;
    if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
    setImageFile(null);
    setImagePreviewUrl("");
    setForm({
      code: selectedProduct.code || "",
      name: selectedProduct.name || "",
      description: selectedProduct.description || "",
      price_coin: selectedProduct.price_coin || 0,
      image_url: selectedProduct.image_url || "",
      stock_quantity: selectedProduct.stock_quantity || 0,
      is_active: Boolean(selectedProduct.is_active),
      sort_order: selectedProduct.sort_order || 0,
    });
  }, [selectedProduct]);

  useEffect(() => () => {
    if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
  }, [imagePreviewUrl]);

  const updateForm = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const startCreate = () => {
    if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
    setSelectedProductId(null);
    setForm(EMPTY_PRODUCT);
    setImageFile(null);
    setImagePreviewUrl("");
    setTab("products");
  };

  const saveProduct = async (event) => {
    event.preventDefault();
    setIsSaving(true);
    setError("");
    setNotice("");
    const payload = {
      ...form,
      code: form.code.trim(),
      name: form.name.trim(),
      description: form.description.trim(),
      image_url: form.image_url.trim() || null,
      price_coin: Number(form.price_coin || 0),
      stock_quantity: Number(form.stock_quantity || 0),
      sort_order: Number(form.sort_order || 0),
    };
    try {
      const saved = selectedProductId
        ? await adminShopApi.updateProductWithImage(selectedProductId, payload, imageFile)
        : await adminShopApi.createProductWithImage(payload, imageFile);
      setNotice(selectedProductId ? "Đã cập nhật sản phẩm." : "Đã thêm sản phẩm.");
      setSelectedProductId(saved.id);
      if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
      setImageFile(null);
      setImagePreviewUrl("");
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể lưu sản phẩm.");
    } finally {
      setIsSaving(false);
    }
  };

  const hideProduct = async (productId) => {
    setError("");
    setNotice("");
    try {
      await adminShopApi.hideProduct(productId);
      setNotice("Đã ẩn sản phẩm.");
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể ẩn sản phẩm.");
    }
  };

  const updateStatus = async (redemptionId, status) => {
    setError("");
    setNotice("");
    try {
      await adminShopApi.updateRedemptionStatus(redemptionId, status);
      setNotice(status === "cancelled" ? "Đã hủy đơn và hoàn Coin nếu cần." : "Đã cập nhật trạng thái đơn.");
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể cập nhật trạng thái.");
    }
  };

  const chooseProductImage = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setError("");
    setNotice("");
    if (imagePreviewUrl) {
      URL.revokeObjectURL(imagePreviewUrl);
    }
    setImageFile(file);
    setImagePreviewUrl(URL.createObjectURL(file));
    setNotice("Đã chọn ảnh. Ảnh sẽ upload khi lưu sản phẩm.");
    event.target.value = "";
  };

  return (
    <AdminShell title="Shop" subtitle="Quản lý sản phẩm đổi Coin và đơn nhận hàng." navItems={adminNavItems}>
      {(notice || error) && (
        <div className={`mb-5 rounded-xl px-4 py-3 text-sm font-semibold ${error ? "bg-rose-50 text-rose-700" : "bg-emerald-50 text-emerald-700"}`}>
          {error || notice}
        </div>
      )}

      <div className="mb-6 flex flex-wrap items-center gap-3">
        <button type="button" onClick={() => setTab("products")} className={`rounded-full px-4 py-2 text-sm font-black ${tab === "products" ? "bg-zinc-950 text-white" : "bg-white text-zinc-600"}`}>Sản phẩm</button>
        <button type="button" onClick={() => setTab("redemptions")} className={`rounded-full px-4 py-2 text-sm font-black ${tab === "redemptions" ? "bg-zinc-950 text-white" : "bg-white text-zinc-600"}`}>Đơn đổi</button>
        <button type="button" onClick={startCreate} className="ml-auto inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-black text-white">
          <Plus size={16} /> Thêm sản phẩm
        </button>
      </div>

      {isLoading ? (
        <div className="rounded-2xl border border-border bg-card p-8 text-sm font-semibold text-muted-foreground">Đang tải...</div>
      ) : tab === "products" ? (
        <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
          <div className="rounded-2xl border border-border bg-card p-4 shadow-sm">
            <div className="space-y-3">
              {products.map((product) => (
                <div key={product.id} className="flex flex-col gap-3 rounded-xl border border-border p-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-black text-zinc-950">{product.name}</h3>
                      <span className="rounded-full bg-amber-50 px-2 py-1 text-xs font-black text-amber-700">{product.price_coin} Coin</span>
                      <span className={`rounded-full px-2 py-1 text-xs font-black ${product.is_active ? "bg-emerald-50 text-emerald-700" : "bg-zinc-100 text-zinc-500"}`}>{product.is_active ? "Hiện" : "Ẩn"}</span>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">{product.description}</p>
                    <p className="mt-1 text-xs font-bold text-zinc-400">Code: {product.code} · Tồn: {product.stock_quantity} · Thứ tự: {product.sort_order}</p>
                  </div>
                  <div className="flex gap-2">
                    <button type="button" onClick={() => setSelectedProductId(product.id)} className="inline-flex items-center gap-2 rounded-xl border border-border px-3 py-2 text-xs font-black text-zinc-700"><PencilSimple size={14} /> Sửa</button>
                    <button type="button" onClick={() => hideProduct(product.id)} className="inline-flex items-center gap-2 rounded-xl border border-rose-200 px-3 py-2 text-xs font-black text-rose-700"><Trash size={14} /> Ẩn</button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <form onSubmit={saveProduct} className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <h2 className="text-lg font-black text-zinc-950">{selectedProductId ? "Sửa sản phẩm" : "Thêm sản phẩm"}</h2>
            <div className="mt-4 space-y-3">
              <input required placeholder="Code" value={form.code} onChange={(event) => updateForm("code", event.target.value)} className="w-full rounded-xl border border-border px-4 py-3 text-sm" />
              <input required placeholder="Tên sản phẩm" value={form.name} onChange={(event) => updateForm("name", event.target.value)} className="w-full rounded-xl border border-border px-4 py-3 text-sm" />
              <textarea placeholder="Mô tả" value={form.description} onChange={(event) => updateForm("description", event.target.value)} className="w-full rounded-xl border border-border px-4 py-3 text-sm" />
              <div className="rounded-xl border border-border p-3">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-black uppercase tracking-[0.18em] text-zinc-500">Ảnh sản phẩm</p>
                    <p className="mt-1 truncate text-xs font-semibold text-zinc-500">{imageFile?.name || form.image_url || "Chưa có ảnh"}</p>
                  </div>
                  <button type="button" onClick={() => imageInputRef.current?.click()} disabled={isSaving} className="rounded-xl border border-border px-4 py-2 text-xs font-black text-zinc-700 disabled:opacity-50">
                    Chọn ảnh
                  </button>
                </div>
                {imagePreviewUrl || form.image_url ? <img src={imagePreviewUrl || form.image_url} alt="Product" className="mt-3 h-32 w-full rounded-xl object-cover" /> : null}
                <input ref={imageInputRef} type="file" accept="image/*" onChange={chooseProductImage} className="hidden" />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <input type="number" min="0" placeholder="Coin" value={form.price_coin} onChange={(event) => updateForm("price_coin", event.target.value)} className="rounded-xl border border-border px-4 py-3 text-sm" />
                <input type="number" min="0" placeholder="Tồn" value={form.stock_quantity} onChange={(event) => updateForm("stock_quantity", event.target.value)} className="rounded-xl border border-border px-4 py-3 text-sm" />
                <input type="number" placeholder="Thứ tự" value={form.sort_order} onChange={(event) => updateForm("sort_order", event.target.value)} className="rounded-xl border border-border px-4 py-3 text-sm" />
              </div>
              <label className="flex items-center gap-2 text-sm font-bold text-zinc-700">
                <input type="checkbox" checked={form.is_active} onChange={(event) => updateForm("is_active", event.target.checked)} /> Hiển thị trong shop
              </label>
            </div>
            <button type="submit" disabled={isSaving} className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-zinc-950 px-4 py-3 text-sm font-black text-white disabled:opacity-50">
              {form.is_active ? <CheckCircle size={16} /> : <ProhibitInset size={16} />}
              {isSaving ? "Đang lưu..." : "Lưu sản phẩm"}
            </button>
          </form>
        </div>
      ) : (
        <div className="rounded-2xl border border-border bg-card p-4 shadow-sm">
          <div className="space-y-3">
            {redemptions.map((item) => (
              <div key={item.id} className="rounded-xl border border-border p-4">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <h3 className="font-black text-zinc-950">#{item.id} · {item.product_name}</h3>
                    <p className="mt-1 text-sm text-muted-foreground">{item.user_email} · {item.price_coin} Coin · {formatDateTime(item.created_at)}</p>
                    <p className="mt-3 text-sm font-bold text-zinc-800">{item.recipient_name} · {item.phone}</p>
                    <p className="mt-1 text-sm text-zinc-600">{item.address}</p>
                    {item.note && <p className="mt-1 text-sm text-zinc-500">Ghi chú: {item.note}</p>}
                    {item.refunded && <p className="mt-2 text-xs font-black uppercase tracking-[0.16em] text-emerald-700">Đã hoàn Coin</p>}
                  </div>
                  <select value={item.status} onChange={(event) => updateStatus(item.id, event.target.value)} className="rounded-xl border border-border px-3 py-2 text-sm font-bold">
                    {statuses.map((status) => <option key={status} value={status}>{status}</option>)}
                  </select>
                </div>
              </div>
            ))}
            {redemptions.length === 0 && <div className="p-6 text-center text-sm font-semibold text-muted-foreground">Chưa có đơn đổi.</div>}
          </div>
        </div>
      )}
    </AdminShell>
  );
};

export default AdminShopPage;
