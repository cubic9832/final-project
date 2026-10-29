import { useEffect, useState } from 'react';
import { getRecommendationOptions } from '../../financialRecommendationApi.js';

export default function useRecommendationOptions() {
  const [options, setOptions] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    getRecommendationOptions(controller.signal).then(value => {
      if (!controller.signal.aborted) setOptions(value);
    }).catch(() => {
      if (!controller.signal.aborted) setError('추천 서버의 입력 항목을 불러오지 못했습니다. 페이지를 새로고침해 다시 시도해 주세요.');
    });
    return () => controller.abort();
  }, []);
  return { options, error };
}
