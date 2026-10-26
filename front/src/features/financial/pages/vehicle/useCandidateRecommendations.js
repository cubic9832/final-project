import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { buildCandidateRecommendation } from '../../buildCandidateRecommendation.js';
import { getFinancialRecommendations } from '../../financialRecommendationApi.js';

export default function useCandidateRecommendations(state) {
  const navigate = useNavigate();
  const [notice, setNotice] = useState('');
  const [recommending, setRecommending] = useState(false);
  const pendingRequest = useRef(null);
  useEffect(() => () => pendingRequest.current?.abort(), []);
  async function showRecommendations() {
    if (pendingRequest.current) return;
    const { request, errors } = buildCandidateRecommendation(state);
    if (!request) {
      setNotice(`입력 정보를 확인해 주세요: ${[...new Set(errors)].join(', ')}`);
      return;
    }
    const controller = new AbortController();
    pendingRequest.current = controller;
    setRecommending(true);
    setNotice('차량별 가격·유지비를 계산하고 있습니다.');
    try {
      const response = await getFinancialRecommendations(request, controller.signal);
      if (!controller.signal.aborted) navigate('/financial/result', { state: { diagnosis: state, result: response } });
    } catch (error) {
      if (!controller.signal.aborted) setNotice(error.response?.data?.detail ?? '분석 서버에 연결하지 못했습니다. 입력은 유지됩니다. 종합 분석 결과 보기를 눌러 다시 시도해 주세요.');
    } finally {
      pendingRequest.current = null;
      if (!controller.signal.aborted) setRecommending(false);
    }
  }

  return { notice, recommending, showRecommendations };
}
