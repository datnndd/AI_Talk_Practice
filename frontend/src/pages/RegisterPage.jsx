import BrandIntro from "../components/BrandIntro";
import RegisterForm from "../components/RegisterForm";

const RegisterPage = () => {
  return (
    <div className="min-h-screen bg-white font-sans antialiased overflow-hidden selection:bg-primary/10 selection:text-primary">
      <main className="flex min-h-screen">
        <BrandIntro />
        <RegisterForm />
      </main>
    </div>
  );
};

export default RegisterPage;
