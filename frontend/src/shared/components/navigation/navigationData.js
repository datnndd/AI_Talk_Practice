import {
  BookOpenText,
  Crown,
  CreditCard,
  ChatCircleText,
  House,
  Medal,
  Notebook,
  Robot,
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

export const learnerSidebarItems = [
  { label: "Luyện nói", path: "/scenarios", icon: ChatCircleText },
  { label: "Lộ trình học", path: "/learn", icon: GraduationCap },
  { label: "Bảng xếp hạng", path: "/leaderboard", icon: Trophy },
  { label: "Cửa hàng", path: "/shop", icon: Storefront },
  { label: "Hồ sơ", path: "/profile", icon: UserCircle },
];

export const learnerMobileItems = [
  { label: "Học", path: "/learn", icon: House },
  { label: "Luyện", path: "/scenarios", icon: Notebook },
  { label: "BXH", path: "/leaderboard", icon: Medal },
  { label: "Shop", path: "/shop", icon: Storefront },
  { label: "Hồ sơ", path: "/profile", icon: UserCircle, usesAvatar: true },
];

export const learnerNavItems = [
  { label: "Luyện nói", path: "/scenarios", icon: BookOpenText },
  { label: "Lộ trình học", path: "/learn", icon: GraduationCap },
  { label: "Bảng xếp hạng", path: "/leaderboard", icon: Trophy },
  { label: "Cửa hàng", path: "/shop", icon: Storefront },
  { label: "Gói học", path: "/subscription", icon: Crown },
  { label: "Hồ sơ", path: "/profile", icon: UserCircle },
];

export const learnerTabItems = [
  { label: "Luyện", path: "/scenarios", icon: BookOpenText },
  { label: "Học", path: "/learn", icon: GraduationCap },
  { label: "BXH", path: "/leaderboard", icon: Trophy },
  { label: "Shop", path: "/shop", icon: Storefront },
  { label: "Pro", path: "/subscription", icon: Crown },
  { label: "Hồ sơ", path: "/profile", icon: UserCircle },
];
export const adminNavItems = [
  { label: "Scenarios", anchor: "#scenario-library", icon: SquaresFour },
  { label: "Queue", anchor: "#generation-queue", icon: Sparkle },
];

export const adminWorkspaceNavItems = [
  { label: "Users", path: "/admin/users", icon: UserList },
  { label: "Scenarios", path: "/admin/scenarios", icon: SquaresFour },
  { label: "Characters", path: "/admin/characters", icon: Robot },
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
