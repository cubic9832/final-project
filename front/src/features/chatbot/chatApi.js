import client from '../../shared/api/client';

export async function sendChatMessage(message, signal) {
  const response = await client.post('/chat-messages', { message }, {
    timeout: 45000,
    signal,
  });
  return response.data.data;
}

export async function getChatHistory(signal) {
  const response = await client.get('/chat-messages', { signal });
  return response.data.data;
}

export async function sendChatGuide(guideId, signal) {
  const response = await client.post('/chat-messages/guides', { guideId }, { signal });
  return response.data.data;
}

export async function clearChatHistory() {
  await client.delete('/chat-messages');
}
