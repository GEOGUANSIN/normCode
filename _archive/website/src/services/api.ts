import axios from 'axios';
import { API_URL } from '../config';
import type { 
  RepositorySetMetadata,
  RepositorySetData,
  ConceptEntry,
  InferenceEntry,
  RunResponse, 
  LogContentResponse,
  FlowData
} from '../types';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

class ApiService {
  // Repository Management
  async fetchRepositorySets(): Promise<RepositorySetMetadata[]> {
    const response = await apiClient.get<RepositorySetMetadata[]>('/repositories');
    return response.data;
  }

  async loadRepositorySet(name: string): Promise<RepositorySetData> {
    const response = await apiClient.get<RepositorySetData>(`/repositories/${name}/data`);
    return response.data;
  }

  async createRepositorySet(metadata: RepositorySetMetadata): Promise<RepositorySetMetadata> {
    const response = await apiClient.post<RepositorySetMetadata>('/repositories', metadata);
    return response.data;
  }

  async deleteRepositorySet(name: string): Promise<void> {
    await apiClient.delete(`/repositories/${name}`);
  }

  // Concept Management
  async getConcepts(repoName: string): Promise<ConceptEntry[]> {
    const response = await apiClient.get<ConceptEntry[]>(`/repositories/${repoName}/concepts`);
    return response.data;
  }

  async addConcept(repoName: string, concept: ConceptEntry): Promise<ConceptEntry> {
    const response = await apiClient.post<ConceptEntry>(`/repositories/${repoName}/concepts`, concept);
    return response.data;
  }

  async updateConcept(repoName: string, conceptId: string, concept: ConceptEntry): Promise<ConceptEntry> {
    const response = await apiClient.put<ConceptEntry>(`/repositories/${repoName}/concepts/${conceptId}`, concept);
    return response.data;
  }

  async deleteConcept(repoName: string, conceptId: string): Promise<void> {
    await apiClient.delete(`/repositories/${repoName}/concepts/${conceptId}`);
  }

  // Inference Management
  async getInferences(repoName: string): Promise<InferenceEntry[]> {
    const response = await apiClient.get<InferenceEntry[]>(`/repositories/${repoName}/inferences`);
    return response.data;
  }

  async addInference(repoName: string, inference: InferenceEntry): Promise<InferenceEntry> {
    const response = await apiClient.post<InferenceEntry>(`/repositories/${repoName}/inferences`, inference);
    return response.data;
  }

  async updateInference(repoName: string, inferenceId: string, inference: InferenceEntry): Promise<InferenceEntry> {
    const response = await apiClient.put<InferenceEntry>(`/repositories/${repoName}/inferences/${inferenceId}`, inference);
    return response.data;
  }

  async deleteInference(repoName: string, inferenceId: string): Promise<void> {
    await apiClient.delete(`/repositories/${repoName}/inferences/${inferenceId}`);
  }

  // Execution
  async runRepositorySet(name: string): Promise<string> {
    const response = await apiClient.post<RunResponse>('/repositories/run', { repository_set_name: name });
    return response.data.log_file;
  }

  async getLogContent(logFilename: string): Promise<string> {
    const response = await apiClient.get<LogContentResponse>(`/logs/${logFilename}`);
    return response.data.content;
  }

  // Global Concepts Management
  async getGlobalConcepts(): Promise<ConceptEntry[]> {
    const response = await apiClient.get<ConceptEntry[]>('/concepts');
    return response.data;
  }

  async addGlobalConcept(concept: ConceptEntry): Promise<ConceptEntry> {
    const response = await apiClient.post<ConceptEntry>('/concepts', concept);
    return response.data;
  }

  async updateGlobalConcept(conceptId: string, concept: ConceptEntry): Promise<ConceptEntry> {
    const response = await apiClient.put<ConceptEntry>(`/concepts/${conceptId}`, concept);
    return response.data;
  }

  async deleteGlobalConcept(conceptId: string): Promise<void> {
    await apiClient.delete(`/concepts/${conceptId}`);
  }

  // Global Inferences Management
  async getGlobalInferences(): Promise<InferenceEntry[]> {
    const response = await apiClient.get<InferenceEntry[]>('/inferences');
    return response.data;
  }

  async addGlobalInference(inference: InferenceEntry): Promise<InferenceEntry> {
    const response = await apiClient.post<InferenceEntry>('/inferences', inference);
    return response.data;
  }

  async updateGlobalInference(inferenceId: string, inference: InferenceEntry): Promise<InferenceEntry> {
    const response = await apiClient.put<InferenceEntry>(`/inferences/${inferenceId}`, inference);
    return response.data;
  }

  async deleteGlobalInference(inferenceId: string): Promise<void> {
    await apiClient.delete(`/inferences/${inferenceId}`);
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
    const response = await apiClient.post<ConceptEntry>(`/repositories/${repoName}/concepts/from_global`, data);
    return response.data;
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
    const response = await apiClient.post<InferenceEntry>(`/repositories/${repoName}/inferences/from_global`, data);
    return response.data;
  }

  // Flow Management
  async getFlow(repoName: string): Promise<FlowData> {
    const response = await apiClient.get<FlowData>(`/repositories/${repoName}/flow`);
    return response.data;
  }

  async saveFlow(repoName: string, flowData: FlowData): Promise<FlowData> {
    const response = await apiClient.put<FlowData>(`/repositories/${repoName}/flow`, flowData);
    return response.data;
  }

  // Graph Management
  async getGraph(repoName: string): Promise<any> {
    const response = await apiClient.get<any>(`/repositories/${repoName}/graph`);
    return response.data;
  }
}

export const apiService = new ApiService();
