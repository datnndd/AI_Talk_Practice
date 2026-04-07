import BrandIntro from "@/features/auth/components/BrandIntro";
import RegisterForm from "@/features/auth/components/RegisterForm";
import { AuthHeader } from "@/shared/components/navigation";

const RegisterPage = () => {
  return (
    <div className="min-h-[100dvh] bg-white font-sans antialiased overflow-hidden selection:bg-indigo-500/10 selection:text-indigo-600">
      <AuthHeader mode="register" />
      <main className="flex min-h-[100dvh] pt-[92px]">
        <BrandIntro />
        <RegisterForm />
      </main>
    </div>
  );
};

export default RegisterPage;
