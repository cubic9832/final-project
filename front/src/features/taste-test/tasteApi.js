import client from '../../shared/api/client';

export const getTasteCatalog = async (signal) => (await client.get('/members/me/taste-test', { signal })).data;
export const getCurrentTaste = async (signal) => {
  const response = await client.get('/members/me/current-taste', { signal });
  return response.status === 204 ? null : response.data;
};
export const putCurrentTaste = async (request) => (await client.put('/members/me/current-taste', request)).data;

export const tasteErrorMessage = (error) => error.response?.data?.detail ?? error.response?.data?.error?.message
  ?? '서버에 연결하지 못했어요. 잠시 후 다시 시도해 주세요.';
