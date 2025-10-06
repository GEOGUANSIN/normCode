import { 
  RepositorySetMetadata,
  RepositorySetData,
  ConceptEntry,
  InferenceEntry,
  RunResponse, 
  LogContentResponse,
  ApiError,
  FlowData
} from '../types';

const BASE_URL = 'http://localhost:8001';
const API_BASE_URL = `${BASE_URL}/api/repositories`;
const CONCEPTS_API = `${BASE_URL}/api/concepts`;
const INFERENCES_API = `${BASE_URL}/api/inferences`;

class ApiService {
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      const error: ApiError = {
        message: errorData.detail || `HTTP error! status: ${response.status}`,
        status: response.status
      };
      throw error;
    }
    return response.json();
  }

  // Repository Management
  async fetchRepositorySets(): Promise<RepositorySetMetadata[]> {
    const response = await fetch(API_BASE_URL);
    return this.handleResponse<RepositorySetMetadata[]>(response);
  }

  async loadRepositorySet(name: string): Promise<RepositorySetData> {
    const response = await fetch(`${API_BASE_URL}/${name}/data`);
    return this.handleResponse<RepositorySetData>(response);
  }

  async createRepositorySet(metadata: RepositorySetMetadata): Promise<RepositorySetMetadata> {
    const response = await fetch(API_BASE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(metadata)
    });
    return this.handleResponse<RepositorySetMetadata>(response);
  }

  async deleteRepositorySet(name: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/${name}`, {
      method: 'DELETE',
    });
    await this.handleResponse(response);
  }

  // Concept Management
  async getConcepts(repoName: string): Promise<ConceptEntry[]> {
    const response = await fetch(`${API_BASE_URL}/${repoName}/concepts`);
    return this.handleResponse<ConceptEntry[]>(response);
  }

  async addConcept(repoName: string, concept: ConceptEntry): Promise<ConceptEntry> {
    const response = await fetch(`${API_BASE_URL}/${repoName}/concepts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(concept)
    });
    return this.handleResponse<ConceptEntry>(response);
  }

  async updateConcept(repoName: string, conceptId: string, concept: ConceptEntry): Promise<ConceptEntry> {
    const response = await fetch(`${API_BASE_URL}/${repoName}/concepts/${conceptId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(concept)
    });
    return this.handleResponse<ConceptEntry>(response);
  }

  async deleteConcept(repoName: string, conceptId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/${repoName}/concepts/${conceptId}`, {
      method: 'DELETE',
    });
    await this.handleResponse(response);
  }

  // Inference Management
  async getInferences(repoName: string): Promise<InferenceEntry[]> {
    const response = await fetch(`${API_BASE_URL}/${repoName}/inferences`);
    return this.handleResponse<InferenceEntry[]>(response);
  }

  async addInference(repoName: string, inference: InferenceEntry): Promise<InferenceEntry> {
    const response = await fetch(`${API_BASE_URL}/${repoName}/inferences`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(inference)
    });
    return this.handleResponse<InferenceEntry>(response);
  }

  async updateInference(repoName: string, inferenceId: string, inference: InferenceEntry): Promise<InferenceEntry> {
    const response = await fetch(`${API_BASE_URL}/${repoName}/inferences/${inferenceId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(inference)
    });
    return this.handleResponse<InferenceEntry>(response);
  }

  async deleteInference(repoName: string, inferenceId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/${repoName}/inferences/${inferenceId}`, {
      method: 'DELETE',
    });
    await this.handleResponse(response);
  }

  // Execution
  async runRepositorySet(name: string): Promise<string> {
    const response = await fetch(`${API_BASE_URL}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repository_set_name: name })
    });
    const result = await this.handleResponse<RunResponse>(response);
    return result.log_file;
  }

  async getLogContent(logFilename: string): Promise<string> {
    const response = await fetch(`${API_BASE_URL}/logs/${logFilename}`);
    const data = await this.handleResponse<LogContentResponse>(response);
    return data.content;
  }

  // Global Concepts Management
  async getGlobalConcepts(): Promise<ConceptEntry[]> {
    const response = await fetch(CONCEPTS_API);
    return this.handleResponse<ConceptEntry[]>(response);
  }

  async addGlobalConcept(concept: ConceptEntry): Promise<ConceptEntry> {
    const response = await fetch(CONCEPTS_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(concept)
    });
    return this.handleResponse<ConceptEntry>(response);
  }

  async updateGlobalConcept(conceptId: string, concept: ConceptEntry): Promise<ConceptEntry> {
    const response = await fetch(`${CONCEPTS_API}/${conceptId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(concept)
    });
    return this.handleResponse<ConceptEntry>(response);
  }

  async deleteGlobalConcept(conceptId: string): Promise<void> {
    const response = await fetch(`${CONCEPTS_API}/${conceptId}`, {
      method: 'DELETE',
    });
    await this.handleResponse(response);
  }

  // Global Inferences Management
  async getGlobalInferences(): Promise<InferenceEntry[]> {
    const response = await fetch(INFERENCES_API);
    return this.handleResponse<InferenceEntry[]>(response);
  }

  async addGlobalInference(inference: InferenceEntry): Promise<InferenceEntry> {
    const response = await fetch(INFERENCES_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(inference)
    });
    return this.handleResponse<InferenceEntry>(response);
  }

  async updateGlobalInference(inferenceId: string, inference: InferenceEntry): Promise<InferenceEntry> {
    const response = await fetch(`${INFERENCES_API}/${inferenceId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(inference)
    });
    return this.handleResponse<InferenceEntry>(response);
  }

  async deleteGlobalInference(inferenceId: string): Promise<void> {
    const response = await fetch(`${INFERENCES_API}/${inferenceId}`, {
      method: 'DELETE',
    });
    await this.handleResponse(response);
  }

  // Add concept from global to repository
  async addConceptFromGlobal(
    repoName: string, 
    data: {
      global_concept_id: string;
      reference_data: any;
      reference_axis_names: string[];
      is_ground_concept: boolean;
      is_final_concept: boolean;
      is_invariant: boolean;
    }
  ): Promise<ConceptEntry> {
    const response = await fetch(`${API_BASE_URL}/${repoName}/concepts/from_global`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return this.handleResponse<ConceptEntry>(response);
  }

  // Add inference from global to repository
  async addInferenceFromGlobal(
    repoName: string,
    data: {
      global_inference_id: string;
      flow_info: any;
      working_interpretation: any;
      start_without_value: boolean;
      start_without_value_only_once: boolean;
      start_without_function: boolean;
      start_without_function_only_once: boolean;
      start_with_support_reference_only: boolean;
    }
  ): Promise<InferenceEntry> {
    const response = await fetch(`${API_BASE_URL}/${repoName}/inferences/from_global`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return this.handleResponse<InferenceEntry>(response);
  }

  // Flow Management
  async getFlow(repoName: string): Promise<FlowData> {
    const response = await fetch(`${API_BASE_URL}/${repoName}/flow`);
    return this.handleResponse<FlowData>(response);
  }

  async saveFlow(repoName: string, flowData: FlowData): Promise<FlowData> {
    const response = await fetch(`${API_BASE_URL}/${repoName}/flow`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(flowData)
    });
    return this.handleResponse<FlowData>(response);
  }
}

export const apiService = new ApiService();
