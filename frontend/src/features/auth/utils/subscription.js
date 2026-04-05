const ACTIVE_SUBSCRIPTION_STATUSES = new Set(["active", "trialing", "trial"]);
const PAID_SUBSCRIPTION_TIERS = new Set(["PRO", "PREMIUM", "SUBSCRIPTION", "ENTERPRISE"]);

export const normalizeSubscription = (subscription) => {
  const tier = String(subscription?.tier || "FREE").toUpperCase();
  const status = String(subscription?.status || "inactive").toLowerCase();
  const features = subscription?.features && typeof subscription.features === "object"
    ? subscription.features
    : {};

  const isPaidTier = PAID_SUBSCRIPTION_TIERS.has(tier);
  const isActive = isPaidTier && ACTIVE_SUBSCRIPTION_STATUSES.has(status);

  return {
    tier,
    status,
    expiresAt: subscription?.expires_at || null,
    features,
    isFree: !isPaidTier,
    isPaidTier,
    isActive,
    isSubscribed: isPaidTier && isActive,
  };
};

export const canAccessSubscriptionFeatures = (user) =>
  Boolean(user?.is_admin) || normalizeSubscription(user?.subscription).isSubscribed;

export const getUserAccessLevel = (user) => {
  if (user?.is_admin) {
    return "ADMIN";
  }

  return canAccessSubscriptionFeatures(user) ? "SUBSCRIPTION" : "FREE";
};

export const getSubscriptionLabel = (subscription) => {
  const normalized = normalizeSubscription(subscription);

  if (normalized.tier === "FREE") {
    return "Free";
  }

  return normalized.tier.charAt(0) + normalized.tier.slice(1).toLowerCase();
};
