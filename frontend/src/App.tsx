import { lazy, Suspense, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { BrowserRouter, Link, Route, Routes, useLocation } from "react-router-dom";
import { PageLoader } from "./components/ui";
import Landing from "./pages/Landing";

const Advisor = lazy(() => import("./pages/Advisor"));
const Quote = lazy(() => import("./pages/Quote"));
const Consent = lazy(() => import("./pages/Consent"));
const Kyc = lazy(() => import("./pages/Kyc"));
const Track = lazy(() => import("./pages/Track"));
const Privacy = lazy(() => import("./pages/Privacy"));
const Backoffice = lazy(() => import("./pages/Backoffice"));

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

function NotFound() {
  const { t } = useTranslation();
  return (
    <div className="app-glow flex min-h-[100dvh] flex-col items-center justify-center gap-4 px-4 text-center">
      <p className="font-display text-7xl font-extrabold text-brand-200">404</p>
      <h1 className="text-xl font-bold">{t("notFound.title")}</h1>
      <Link to="/" className="btn-primary">{t("notFound.home")}</Link>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <ScrollToTop />
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/advisor" element={<Advisor />} />
          <Route path="/quote/:id" element={<Quote />} />
          <Route path="/consent/:orderId" element={<Consent />} />
          <Route path="/kyc/:orderId" element={<Kyc />} />
          <Route path="/track" element={<Track />} />
          <Route path="/track/:orderId" element={<Track />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/backoffice" element={<Backoffice />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
