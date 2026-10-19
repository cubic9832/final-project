import { useEffect } from 'react';
import { Route, Routes } from 'react-router-dom';

import { refreshAccessToken } from './shared/api/tokenRefresh';
import Layout from './components/Layout';
import RequireAuth from './components/RequireAuth';
import CompanyDetailPage from './features/company/pages/detail/CompanyDetailPage';
import CompanyListPage from './features/company/pages/list/CompanyListPage';
import AboutPage from './pages/about/AboutPage';
import HomePage from './pages/home/HomePage';
import LoginPage from './pages/login/LoginPage';
import FinancialPage from './features/financial/pages/overview/FinancialPage';
import FinancialAssetsPage from './features/financial/pages/assets/FinancialAssetsPage';
import FinancialCreditPage from './features/financial/pages/credit/FinancialCreditPage';
import FinancialVehiclePage from './features/financial/pages/vehicle/FinancialVehiclePage';
import FinancialReviewPage from './features/financial/pages/review/FinancialReviewPage';
import FinancialResultPage from './features/financial/pages/result/FinancialResultPage';
import FinancialRecommendationsPage from './features/financial/pages/recommendations/FinancialRecommendationsPage';
import AdminPage from './pages/admin/AdminPage';
import MyPage from './pages/mypage/MyPage';
import NotFound from './pages/not-found/NotFound';
import PredictPage from './pages/predict/PredictPage';
import SignupPage from './pages/signup/SignupPage';
import VehicleCatalogGate from './features/vehicle/components/VehicleCatalogGate';
import { VehicleProvider } from './features/vehicle/VehicleContext';
import { VehicleSearchPage } from './features/vehicle/pages/search/VehicleSearchPage';
import { VehicleResultsPage } from './features/vehicle/pages/results/VehicleResultsPage';
import VehicleDetailPage from './features/vehicle/pages/detail/VehicleDetailPage';
import VehicleComparePage from './features/vehicle/pages/compare/VehicleComparePage';
import VehicleSimulationPage from './features/vehicle/pages/simulation/VehicleSimulationPage';
import useAuthStore from './stores/useAuthStore';

function App() {
  // 앱이 처음 열릴 때 한 번: refresh token 쿠키가 있으면 로그인 상태를 되살린다 (새로고침 · 브라우저 재시작 후 로그인 유지)
  useEffect(() => {
    refreshAccessToken()
      .catch(() => {}) // 쿠키가 없거나 만료 → 로그아웃 상태로 시작 (정상)
      .finally(() => useAuthStore.getState().setInitialized());
  }, []);

  return (
    <VehicleProvider>
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/login" element={<LoginPage />} />
        {/* 로그인이 필요한 화면 — 로그인 전이면 RequireAuth 가 /login 으로 보낸다 */}
        <Route element={<RequireAuth />}>
          <Route path="/mypage" element={<MyPage />} />
        </Route>
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/financial" element={<FinancialPage />} />
        <Route path="/financial/assets" element={<FinancialAssetsPage />} />
        <Route path="/financial/credit" element={<FinancialCreditPage />} />
        <Route path="/financial/vehicle" element={<FinancialVehiclePage />} />
        <Route path="/financial/review" element={<FinancialReviewPage />} />
        <Route path="/financial/result" element={<FinancialResultPage />} />
        <Route path="/financial/recommendations" element={<FinancialRecommendationsPage />} />
        <Route path="/companies" element={<CompanyListPage />} />
        <Route path="/companies/:code" element={<CompanyDetailPage />} />
        <Route path="/search" element={<VehicleCatalogGate><VehicleSearchPage /></VehicleCatalogGate>} />
        <Route path="/vehicles" element={<VehicleCatalogGate><VehicleResultsPage /></VehicleCatalogGate>} />
        <Route path="/vehicles/compare" element={<VehicleCatalogGate><VehicleComparePage /></VehicleCatalogGate>} />
        <Route path="/vehicles/:id" element={<VehicleCatalogGate><VehicleDetailPage /></VehicleCatalogGate>} />
        <Route path="/vehicles/:id/simulation" element={<VehicleCatalogGate><VehicleSimulationPage /></VehicleCatalogGate>} />
        <Route path="/predict" element={<PredictPage />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
    </VehicleProvider>
  );
}

export default App;
