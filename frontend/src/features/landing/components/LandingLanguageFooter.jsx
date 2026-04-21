import { CaretLeft, CaretRight } from "@phosphor-icons/react";

const languages = [
  { name: "English", icon: "https://lh3.googleusercontent.com/aida-public/AB6AXuCtPmumt2IF66HX3P_PNGnNyZzS0F5ZXRiVCrUrLFNsIBSp_h9PGvirVHthw9EMUWWNgc_lXgO4O8zi8z3hclYMs538Gricea7sJ3lvk7C7KQB1q_c5CwBXKgLK9MXJUyhm0Rmf8v8tFTCQRCEa1lQt_AJipkNIF33TyJNGv7DHKFd_dBnXvJ6B7UfuHFdS0g5npH0fwj-5RskOGy797cZGCqiWA3omrBSOqQwBT_YIKEZzMj8_KuRdcoJltrnATyDV9nfuBLlsOW9f" },
  { name: "Spanish", icon: "https://lh3.googleusercontent.com/aida-public/AB6AXuBJPnlNR4xvG3L36mB1lq3fOmMzaLBUvvYMkiz0GXfzbO2aSH1ZIzWbC-1w9V8W7cZE1u4XUmwXVkIoa8y0Aa30tOa7TgK6nVFANaD-qFLq1xsNYsSfj31n7tBnRDctsggyKZdEBBmY4zslmEEWAAJh9u-3jhyiA9bU9y8Hd_upd-rktQOLIbDE_uQo1OOnD2gDVtHWVXi684ceIr6pXHxPV6KNPewMwUNcsnwACymL0lTqxRnKiHjE-8gPb8LA2jZhkbrgY4sf_yBE" },
  { name: "French", icon: "https://lh3.googleusercontent.com/aida-public/AB6AXuDnxxn-sj7gm-b70yvP9OWBtgO06SDbzqTUc4d0_7sIZOmvWwh_z3MhxK94BmY_HoQH6ddX-P2jKXWbco_ihqPK-3UdJHPakv8Tc8DvF8P004UO37Fb0aqJ6mP1kG7hHjIBy1WTyotNiWetyusFguzSsRWwUcHI3kSj32_aWCxScqquwLrOEur2IP1mJfaUQWeeuv_fYJpPO04qdzGuw0Q_YjBsRxAHMZzaGDLlsGUJ6ZiD2CFC0cHptkVLQ4A6aK-xEmoFSdLOXVWG" },
  { name: "German", icon: "https://lh3.googleusercontent.com/aida-public/AB6AXuCmst9s34aEdz5uLTeA4l_97Q7350dLf5EBhoChOK8OqNwDrJwRjp58iMveGYOtgeUjMTN9QX4nde6oKlU_nVprLjL-2wgBGGZMMXdKfYCfzLqj6lNOlMJ5uVecT_jABy9JfeofQhdhm1HkfW9xvz4LypcmjViuJyC8YimQ8dzdUpcr1fYZQ9FtRcumF2vlrGAXIEsRp9eBDA7WMlCkx5JMIAP3Tl2mUdKTlMaB7Po157v7quRzsWCC7ARG5BWq5uVOJPrFLti11q74" },
  { name: "Italian", icon: "https://lh3.googleusercontent.com/aida-public/AB6AXuA3YmhAix5F0np-srZjvpZRpxySmda4KFNUacmQ7slKL_oBORcbfM35rexEF_F7jmv1HDTSqeac9LgnjVq-636-ZEuOMo47klN6X93I26O3w-7KXAVw6SS7wI9V8cpVydcM8iltrsnw-uXnnA8pj2p4Dz0vJStGTL_8mQ2QooU7z-yz8MonLaxraMPZ-uEImbGVU9msJZYPO-YqO9hIZmK2xqbSa3qrcnrMHMeJdV8qhJoxLgw0RcXeFMAO01dZw8zcrKps-p9HieXv" },
  { name: "Portuguese", icon: "https://lh3.googleusercontent.com/aida-public/AB6AXuAfbHMaH4mUxo3HI2nLtdLstM1mRh-Pm1MW5YOVL1a6lAQHXuM4VYTfXuvVojYz93X1h8n81M90MAYtr7QIzTy4HuRVzy8nu9qXn7d_sDQSeLbCGN32hJys9Mbq-Ipi0u42sleR1nmMSE_A43jcJwNkZFrKTv_9YS95fsg5nk4nhT7sqcKIO4CLqaGbEUCCCsjdo6daj5LsCMPikPNzDef9bP5byznVVyyjCSLGiPhot001or8iOgzAnwyNx-K89qnGUU8uopA8bEI-" }
];

const LandingLanguageFooter = () => {
  return (
    <footer className="border-t border-duo-gray mt-auto bg-white py-8">
      <div className="max-w-7xl mx-auto px-4 relative">
        {/* Carousel Arrows */}
        <button className="absolute left-4 top-1/2 -translate-y-1/2 text-duo-muted hover:text-duo-text transition-colors">
          <CaretLeft weight="bold" className="w-8 h-8" />
        </button>
        <button className="absolute right-4 top-1/2 -translate-y-1/2 text-duo-muted hover:text-duo-text transition-colors">
          <CaretRight weight="bold" className="w-8 h-8" />
        </button>

        {/* Language List */}
        <div className="flex flex-wrap justify-center items-center gap-8 md:gap-12 px-12">
          {languages.map((lang) => (
            <div 
              key={lang.name}
              className="flex items-center space-x-3 cursor-pointer group"
            >
              <img 
                alt={`${lang.name} Flag`} 
                className="w-8 h-6 rounded shadow-sm object-cover transition-transform group-hover:scale-110" 
                src={lang.icon}
              />
              <span className="text-sm font-bold text-duo-header-text group-hover:text-duo-text transition-colors uppercase tracking-wider">
                {lang.name}
              </span>
            </div>
          ))}
        </div>
      </div>
    </footer>
  );
};

export default LandingLanguageFooter;
