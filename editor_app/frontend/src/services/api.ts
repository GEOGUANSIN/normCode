import { 
  RepositorySet, 
  RepositorySetResponse, 
  RepositorySetDetailResponse, 
  RunRepositoryResponse, 
  LogContentResponse,
  ApiError 
} from '../types';

const API_BASE_URL = '/api/repositories';

class ApiService {
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error: ApiError = {
        message: `HTTP error! status: ${response.status}`,
        status: response.status
      };
      throw error;
    }
    return response.json();
  }

  async fetchRepositorySets(): Promise<string[]> {
    try {
      const response = await fetch(API_BASE_URL);
      const data: RepositorySetResponse = await this.handleResponse(response);
      return data.repository_set_names;
    } catch (error) {
      console.error("Error fetching repository sets:", error);
      throw new Error("Failed to fetch repository sets. Is the backend running?");
    }
  }

  async loadRepositorySet(name: string): Promise<RepositorySet> {
    try {
      const response = await fetch(`${API_BASE_URL}/${name}`);
      const data: RepositorySetDetailResponse = await this.handleResponse(response);
      return data.repository_set;
    } catch (error) {
      console.error(`Error loading repository set ${name}:`, error);
      throw new Error(`Failed to load repository set ${name}.`);
    }
  }

  async saveRepositorySet(repoSet: RepositorySet): Promise<RepositorySet> {
    try {
      const response = await fetch(API_BASE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(repoSet)
      });
      return await this.handleResponse(response);
    } catch (error) {
      console.error("Error saving repository set:", error);
      throw new Error("Failed to save repository set.");
    }
  }

  async deleteRepositorySet(name: string): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/${name}`, {
        method: 'DELETE',
      });
      await this.handleResponse(response);
    } catch (error) {
      console.error(`Error deleting repository set ${name}:`, error);
      throw new Error(`Failed to delete repository set ${name}.`);
    }
  }

  async runRepositorySet(name: string): Promise<string> {
    try {
      const response = await fetch(`${API_BASE_URL}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repository_set_name: name })
      });
      const result: RunRepositoryResponse = await this.handleResponse(response);
      return result.log_file;
    } catch (error) {
      console.error(`Error running repository set ${name}:`, error);
      throw new Error(`Failed to run repository set ${name}.`);
    }
  }

  async getLogContent(logFilename: string): Promise<string> {
    try {
      const response = await fetch(`${API_BASE_URL}/logs/${logFilename}`);
      if (!response.ok) {
        // If log file not found, it might still be generating
        console.warn(`Log file ${logFilename} not yet available or error: ${response.status}`);
        return '';
      }
      const data: LogContentResponse = await this.handleResponse(response);
      return data.content;
    } catch (error) {
      console.error(`Error fetching log content for ${logFilename}:`, error);
      throw error;
    }
  }
}

export const apiService = new ApiService();
