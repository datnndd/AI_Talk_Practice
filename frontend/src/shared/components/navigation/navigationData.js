import {
  BookOpenText,
  Crown,
  CreditCard,
  HouseLine,
  Sparkle,
  Trophy,
  SquaresFour,
  UserList,
  UserCircle,
  GraduationCap,
  Storefront,
} from "@phosphor-icons/react";

export const publicNavItems = [
  { label: "Method", href: "#methodology" },
  { label: "Features", href: "#features" },
  { label: "Pricing", href: "#pricing" },
];

export const learnerNavItems = [
  { label: "Tổng quan", path: "/dashboard", icon: HouseLine },
  { label: "Học tập", path: "/learn", icon: GraduationCap },
  { label: "Bảng xếp hạng", path: "/leaderboard", icon: Trophy },
  { label: "Thực hành", path: "/topics", icon: BookOpenText },
  { label: "Cửa hàng", path: "/shop", icon: Storefront },
  { label: "Gói học", path: "/subscription", icon: Crown },
  { label: "Hồ sơ", path: "/profile", icon: UserCircle },
];

export const learnerTabItems = [
  { label: "Tổng quan", path: "/dashboard", icon: HouseLine },
  { label: "Học tập", path: "/learn", icon: GraduationCap },
  { label: "Bảng xếp hạng", path: "/leaderboard", icon: Trophy },
  { label: "Thực hành", path: "/topics", icon: BookOpenText },
  { label: "Cửa hàng", path: "/shop", icon: Storefront },
  { label: "Gói học", path: "/subscription", icon: Crown },
  { label: "Hồ sơ", path: "/profile", icon: UserCircle },
];

export const adminNavItems = [
  { label: "Scenarios", anchor: "#scenario-library", icon: SquaresFour },
  { label: "Queue", anchor: "#generation-queue", icon: Sparkle },
];

export const adminWorkspaceNavItems = [
  { label: "Users", path: "/admin/users", icon: UserList },
  { label: "Scenarios", path: "/admin/scenarios", icon: SquaresFour },
  { label: "Curriculum", path: "/admin/curriculum", icon: GraduationCap },
  { label: "Payments", path: "/admin/payments", icon: CreditCard },
];

export const formatPlanLabel = (isSubscribed, subscriptionTier) => {
  if (!isSubscribed) {
    return "Free";
  }

  if (!subscriptionTier) {
    return "Active";
  }

  return subscriptionTier.charAt(0) + subscriptionTier.slice(1).toLowerCase();
};

export const isRouteActive = (currentPath, targetPath) => {
  if (!targetPath) {
    return false;
  }

  if (currentPath === targetPath) {
    return true;
  }

  if (targetPath === "/") {
    return currentPath === "/";
  }

  return currentPath.startsWith(`${targetPath}/`);
};
