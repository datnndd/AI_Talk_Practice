import BrandIntro from "../components/BrandIntro";
import AuthForm from "../components/AuthForm";

const LoginPage = () => {
  return (
    <div className="min-h-screen bg-white font-sans antialiased overflow-hidden selection:bg-primary/10 selection:text-primary">
      <main className="flex min-h-screen">
        <BrandIntro />
        <AuthForm />
      </main>
    </div>
  );
};

export default LoginPage;
