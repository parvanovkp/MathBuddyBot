export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  try {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8080';
    
    const response = await fetch(`${backendUrl}/start_session`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error('Backend API request failed');
    }

    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    console.error('Error starting new session:', error);
    res.status(500).json({ error: 'Error starting new session' });
  }
}