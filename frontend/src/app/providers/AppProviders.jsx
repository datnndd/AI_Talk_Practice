import { GoogleOAuthProvider } from "@react-oauth/google";

import { AuthProvider } from "@/features/auth/context/AuthContext";

const GOOGLE_CLIENT_ID =
  import.meta.env.VITE_GOOGLE_CLIENT_ID || "your-google-client-id-here.apps.googleusercontent.com";

const AppProviders = ({ children }) => {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthProvider>{children}</AuthProvider>
    </GoogleOAuthProvider>
  );
};

export default AppProviders;
