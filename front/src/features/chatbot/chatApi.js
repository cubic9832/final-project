import client from '../../shared/api/client';

export async function sendChatMessage(message, history, signal) {
  const response = await client.post('/chat-messages', { message, history }, {
    timeout: 60000,
    signal,
  });
  return response.data.data;
}
