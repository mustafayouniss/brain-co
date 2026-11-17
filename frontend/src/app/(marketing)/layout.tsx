import { Navbar } from "@/components/marketing/navbar";
import { Footer } from "@/components/marketing/footer";

export default function MarketingLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="flex min-h-dvh flex-col bg-[#020409] text-white selection:bg-cyan-500/30 selection:text-cyan-100 antialiased overflow-x-hidden">
      <Navbar />
      <main id="main" className="flex-1 w-full">
        {children}
      </main>
      <Footer />
    </div>
  );
}
