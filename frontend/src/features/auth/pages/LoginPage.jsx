import BrandIntro from "@/features/auth/components/BrandIntro";
import AuthForm from "@/features/auth/components/AuthForm";

const LoginPage = () => {
  return (
    <div className="min-h-[100dvh] bg-white font-sans antialiased overflow-hidden selection:bg-indigo-500/10 selection:text-indigo-600">
      <main className="flex min-h-[100dvh]">
        <BrandIntro />
        <AuthForm />
      </main>
    </div>
  );
};

export default LoginPage;
