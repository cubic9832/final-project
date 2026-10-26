import { Navigate, useLocation } from 'react-router-dom';

export default function FinancialReviewPage() {
  const { state } = useLocation();
  return <Navigate to={state?.values ? '/financial/vehicle' : '/financial'} state={state} replace />;
}
