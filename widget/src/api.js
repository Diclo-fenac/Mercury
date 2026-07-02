export class SearchAPI {
  constructor(endpoint, apiKey) {
    this.endpoint = endpoint.replace(/\/$/, '');
    this.apiKey = apiKey;
  }

  async search(query, limit = 5) {
    try {
      const response = await fetch(`${this.endpoint}/api/v1/search/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey
        },
        body: JSON.stringify({ query, limit })
      });
      
      if (!response.ok) throw new Error('Search failed');
      return await response.json();
    } catch (err) {
      console.error('[Mercury] API Error:', err);
      return { success: false, results: [] };
    }
  }

  async getConfig() {
    try {
      const response = await fetch(`${this.endpoint}/api/v1/search/config`, {
        headers: { 'X-API-Key': this.apiKey }
      });
      if (!response.ok) return null;
      const data = await response.json();
      return data.success ? data.config : null;
    } catch (err) {
      console.error('[Mercury] Config Error:', err);
      return null;
    }
  }

  async chat(message, sessionId) {
    try {
      const response = await fetch(`${this.endpoint}/api/v1/search/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey
        },
        body: JSON.stringify({ message, session_id: sessionId })
      });
      if (!response.ok) throw new Error('Chat failed');
      return await response.json();
    } catch (err) {
      console.error('[Mercury] Chat Error:', err);
      return { answer: "There was an error communicating with the AI server." };
    }
  }
}
