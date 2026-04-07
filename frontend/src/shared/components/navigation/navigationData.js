import {
  BookOpenText,
  Crown,
  HouseLine,
  Sparkle,
  SquaresFour,
  UserCircle,
} from "@phosphor-icons/react";

export const publicNavItems = [
  { label: "Method", href: "#methodology" },
  { label: "Features", href: "#features" },
  { label: "Pricing", href: "#pricing" },
];

export const learnerNavItems = [
  { label: "Dashboard", path: "/dashboard", icon: HouseLine },
  { label: "Topics", path: "/topics", icon: BookOpenText },
  { label: "Plan", path: "/subscription", icon: Crown },
  { label: "Profile", path: "/profile", icon: UserCircle },
];

export const learnerTabItems = [
  { label: "Dashboard", path: "/dashboard", icon: HouseLine },
  { label: "Topics", path: "/topics", icon: BookOpenText },
  { label: "Plan", path: "/subscription", icon: Crown },
  { label: "Profile", path: "/profile", icon: UserCircle },
];

export const adminNavItems = [
  { label: "Scenarios", anchor: "#scenario-library", icon: SquaresFour },
  { label: "Queue", anchor: "#generation-queue", icon: Sparkle },
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
