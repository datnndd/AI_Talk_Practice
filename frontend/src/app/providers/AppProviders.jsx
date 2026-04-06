import { GoogleOAuthProvider } from "@react-oauth/google";

import { AuthProvider } from "@/features/auth/context/AuthContext";
import { ThemeProvider } from "@/shared/context/ThemeContext";

const GOOGLE_CLIENT_ID =
  import.meta.env.VITE_GOOGLE_CLIENT_ID || "your-google-client-id-here.apps.googleusercontent.com";

const AppProviders = ({ children }) => {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <ThemeProvider>
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </GoogleOAuthProvider>
  );
};

export default AppProviders;
