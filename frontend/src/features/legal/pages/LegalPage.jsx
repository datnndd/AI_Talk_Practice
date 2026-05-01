import { Link } from "react-router-dom";
import { ArrowLeft, ShieldCheck } from "@phosphor-icons/react";

import { useSiteSettings } from "@/shared/hooks/useSiteSettings";

const legalContent = {
  terms: {
    label: "Điều khoản sử dụng",
    title: "Terms of Service",
    description: "Các điều khoản áp dụng khi bạn sử dụng nền tảng luyện nói tiếng Anh với AI.",
    sections: [
      {
        title: "1. Chấp nhận điều khoản",
        body: "Khi tạo tài khoản, đăng nhập hoặc sử dụng dịch vụ, bạn đồng ý tuân thủ các điều khoản này. Nếu không đồng ý, bạn nên ngừng sử dụng dịch vụ.",
      },
      {
        title: "2. Tài khoản người dùng",
        body: "Bạn chịu trách nhiệm bảo mật thông tin đăng nhập và mọi hoạt động diễn ra trong tài khoản của mình. Thông tin đăng ký cần chính xác để chúng tôi hỗ trợ bạn khi cần.",
      },
      {
        title: "3. Sử dụng dịch vụ học tiếng Anh với AI",
        body: "Dịch vụ cung cấp bài luyện nói, hội thoại, phản hồi phát âm và nội dung học tập do hệ thống hỗ trợ. Kết quả đánh giá chỉ nhằm mục đích học tập, không thay thế chứng chỉ hoặc đánh giá chuyên môn chính thức.",
      },
      {
        title: "4. Subscription và thanh toán",
        body: "Một số tính năng có thể yêu cầu gói trả phí. Giá, quyền lợi và thời hạn gói sẽ được hiển thị trước khi thanh toán. Bạn chịu trách nhiệm kiểm tra thông tin gói trước khi xác nhận giao dịch.",
      },
      {
        title: "5. Hành vi bị cấm",
        body: "Bạn không được lạm dụng hệ thống, cố gắng truy cập trái phép, sao chép nội dung quy mô lớn, gây gián đoạn dịch vụ, hoặc sử dụng dịch vụ cho mục đích vi phạm pháp luật hay quyền của người khác.",
      },
      {
        title: "6. Giới hạn trách nhiệm",
        body: "Chúng tôi cố gắng duy trì dịch vụ ổn định và chính xác, nhưng không bảo đảm dịch vụ luôn không lỗi hoặc phù hợp với mọi mục đích cụ thể. Bạn sử dụng dịch vụ theo quyết định của mình.",
      },
      {
        title: "7. Thay đổi dịch vụ và điều khoản",
        body: "Chúng tôi có thể cập nhật tính năng, nội dung hoặc điều khoản để cải thiện sản phẩm và đáp ứng yêu cầu vận hành. Phiên bản mới sẽ có hiệu lực khi được đăng tải trên trang này.",
      },
      {
        title: "8. Liên hệ",
        body: "Nếu có câu hỏi về điều khoản sử dụng, vui lòng liên hệ đội ngũ hỗ trợ qua thông tin được công bố trên website.",
      },
    ],
  },
  privacy: {
    label: "Chính sách bảo mật",
    title: "Privacy Policy",
    description: "Cách chúng tôi thu thập, sử dụng và bảo vệ dữ liệu khi bạn học cùng AI.",
    sections: [
      {
        title: "1. Dữ liệu tài khoản",
        body: "Chúng tôi có thể thu thập email, thông tin đăng nhập, trạng thái tài khoản và các thiết lập bạn cung cấp để tạo tài khoản, đăng nhập và vận hành dịch vụ.",
      },
      {
        title: "2. Tiến độ học tập",
        body: "Hệ thống có thể lưu bài học đã hoàn thành, điểm luyện tập, lịch sử phiên học, gói đăng ký và các chỉ số tiến bộ để cá nhân hóa trải nghiệm học.",
      },
      {
        title: "3. Audio và phát âm",
        body: "Khi bạn dùng tính năng ghi âm hoặc chấm phát âm, âm thanh và dữ liệu liên quan có thể được xử lý để tạo phản hồi, điểm số và cải thiện trải nghiệm luyện nói.",
      },
      {
        title: "4. Cookie và local storage",
        body: "Website có thể dùng cookie, local storage hoặc công nghệ tương tự để ghi nhớ phiên đăng nhập, tùy chọn giao diện và dữ liệu cần thiết cho trải nghiệm sản phẩm.",
      },
      {
        title: "5. Mục đích xử lý dữ liệu",
        body: "Dữ liệu được dùng để cung cấp dịch vụ, xác thực người dùng, cá nhân hóa bài học, xử lý thanh toán, hỗ trợ khách hàng, bảo vệ hệ thống và cải thiện chất lượng sản phẩm.",
      },
      {
        title: "6. Chia sẻ với nhà cung cấp dịch vụ",
        body: "Chúng tôi có thể chia sẻ dữ liệu cần thiết với nhà cung cấp hạ tầng, xác thực, thanh toán, phân tích hoặc AI để vận hành các tính năng liên quan. Các bên này chỉ nhận dữ liệu cần cho mục đích cung cấp dịch vụ.",
      },
      {
        title: "7. Bảo mật dữ liệu",
        body: "Chúng tôi áp dụng các biện pháp kỹ thuật và tổ chức hợp lý để bảo vệ dữ liệu. Tuy vậy, không phương thức truyền tải hoặc lưu trữ nào an toàn tuyệt đối.",
      },
      {
        title: "8. Quyền của người dùng",
        body: "Bạn có thể yêu cầu truy cập, chỉnh sửa hoặc xóa một số dữ liệu cá nhân theo khả năng hỗ trợ của hệ thống và yêu cầu pháp luật áp dụng.",
      },
      {
        title: "9. Liên hệ",
        body: "Nếu có câu hỏi về quyền riêng tư hoặc dữ liệu cá nhân, vui lòng liên hệ đội ngũ hỗ trợ qua thông tin được công bố trên website.",
      },
    ],
  },
};

const LegalPage = ({ type }) => {
  const settings = useSiteSettings();
  const content = legalContent[type];
  const brandName = settings.brandName || "Buddy Talk";

  return (
    <main className="relative min-h-screen overflow-x-hidden bg-[#f8fbff] px-5 py-8 text-[#24324a] selection:bg-brand-blue/10 selection:text-brand-blue lg:px-8">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_18%_18%,rgba(136,223,70,0.16),transparent_34%),radial-gradient(circle_at_82%_12%,rgba(52,219,197,0.16),transparent_30%),linear-gradient(180deg,rgba(255,255,255,0.86),rgba(244,253,255,0.82))]" />

      <div className="mx-auto max-w-4xl">
        <Link to="/" className="mb-8 inline-flex items-center gap-2 rounded-full border border-white/80 bg-white/70 px-4 py-2 text-sm font-black text-[#2f496b] shadow-sm backdrop-blur transition hover:border-[#34DBC5]/50 hover:text-[#1f8f83]">
          <ArrowLeft size={16} weight="bold" />
          Về trang chủ
        </Link>

        <article className="rounded-[2rem] border border-white/85 bg-white/78 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur-[20px] md:p-10">
          <header className="border-b border-[#d7e4ef] pb-8">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-brand-green/20 bg-brand-green/10 px-4 py-2 text-xs font-black uppercase tracking-[0.2em] text-brand-green-dark">
              <ShieldCheck size={16} weight="duotone" />
              {content.label}
            </div>
            <h1 className="text-4xl font-black tracking-tighter text-[#20314a] md:text-5xl">{content.title}</h1>
            <p className="mt-4 max-w-2xl text-base font-semibold leading-7 text-[#667394]">{content.description}</p>
            <p className="mt-5 text-sm font-bold text-[#667394]">Cập nhật lần cuối: 01/05/2026</p>
          </header>

          <div className="mt-8 space-y-7">
            <p className="rounded-2xl bg-[#f2fbff] p-5 text-sm font-semibold leading-7 text-[#4c607c]">
              Tài liệu này là bản mẫu chính sách sản phẩm cho {brandName} và mô tả cách dịch vụ được vận hành cho người dùng.
            </p>
            {content.sections.map((section) => (
              <section key={section.title} className="space-y-3">
                <h2 className="text-xl font-black tracking-tight text-[#20314a]">{section.title}</h2>
                <p className="text-sm font-medium leading-7 text-[#5c6f8d] md:text-base">{section.body}</p>
              </section>
            ))}
          </div>
        </article>
      </div>
    </main>
  );
};

export default LegalPage;
