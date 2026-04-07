import BrandIntro from "@/features/auth/components/BrandIntro";
import AuthForm from "@/features/auth/components/AuthForm";
import { AuthHeader } from "@/shared/components/navigation";

const LoginPage = () => {
  return (
    <div className="min-h-[100dvh] bg-white font-sans antialiased overflow-hidden selection:bg-indigo-500/10 selection:text-indigo-600">
      <AuthHeader mode="login" />
      <main className="flex min-h-[100dvh] pt-[92px]">
        <BrandIntro />
        <AuthForm />
      </main>
    </div>
  );
};

export default LoginPage;
