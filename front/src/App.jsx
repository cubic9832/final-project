import { Route, Routes } from 'react-router-dom';

import Layout from './components/Layout';
import CompanyDetailPage from './pages/CompanyDetailPage';
import CompanyListPage from './pages/CompanyListPage';
import HomePage from './pages/HomePage';
import NotFound from './pages/NotFound';
import PredictPage from './pages/PredictPage';
import SearchPage from './pages/SearchPage';

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/companies" element={<CompanyListPage />} />
        <Route path="/companies/:code" element={<CompanyDetailPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/predict" element={<PredictPage />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default App;