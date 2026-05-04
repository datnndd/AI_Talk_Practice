import {
  BookOpenText,
  Crown,
  CreditCard,
  HouseLine,
  Sparkle,
  Robot,
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
  { label: "Luy?n n?i", path: "/dashboard", icon: BookOpenText },
  { label: "L? tr?nh h?c", path: "/learn", icon: GraduationCap },
  { label: "B?ng x?p h?ng", path: "/leaderboard", icon: Trophy },
  { label: "C?a h?ng", path: "/shop", icon: Storefront },
  { label: "G?i h?c", path: "/subscription", icon: Crown },
  { label: "H? s?", path: "/profile", icon: UserCircle },
];
export const learnerTabItems = [
  { label: "Luy?n", path: "/dashboard", icon: BookOpenText },
  { label: "H?c", path: "/learn", icon: GraduationCap },
  { label: "BXH", path: "/leaderboard", icon: Trophy },
  { label: "Shop", path: "/shop", icon: Storefront },
  { label: "Pro", path: "/subscription", icon: Crown },
  { label: "H? s?", path: "/profile", icon: UserCircle },
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
