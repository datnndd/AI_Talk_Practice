import AuthCard from "@/features/auth/components/AuthCard";

const RegisterPage = () => {
  return (
    <div className="min-h-screen bg-[#fafafa] selection:bg-brand-blue/10 selection:text-brand-blue">
      <AuthCard mode="register" />
    </div>
  );
};

export default RegisterPage;
