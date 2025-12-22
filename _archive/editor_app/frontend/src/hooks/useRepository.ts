import { useState, useEffect, useCallback } from 'react';
import { RepositorySetMetadata, ConceptEntry, InferenceEntry } from '../types';
import { apiService } from '../services/api';
import { MessageType } from './useMessage';

export const useRepository = (showMessage: (type: MessageType, text: string) => void) => {
  const [repositories, setRepositories] = useState<RepositorySetMetadata[]>([]);
  const [selectedRepoName, setSelectedRepoName] = useState<string>('');
  const [concepts, setConcepts] = useState<ConceptEntry[]>([]);
  const [inferences, setInferences] = useState<InferenceEntry[]>([]);
  const [flowData, setFlowData] = useState<{ nodes: any[]; edges: any[] }>({ nodes: [], edges: [] });
  const [graphData, setGraphData] = useState<any>(null);

  const loadRepositoryList = useCallback(async () => {
    try {
      const repos = await apiService.fetchRepositorySets();
      setRepositories(repos);
    } catch (error) {
      showMessage('error', 'Failed to load repositories');
    }
  }, [showMessage]);

  const loadRepositoryData = useCallback(async () => {
    if (!selectedRepoName) return;
    try {
      const [conceptsData, inferencesData] = await Promise.all([
        apiService.getConcepts(selectedRepoName),
        apiService.getInferences(selectedRepoName)
      ]);
      setConcepts(conceptsData);
      setInferences(inferencesData);
      
      // Load flow data
      try {
        const flowDataResult = await apiService.getFlow(selectedRepoName);
        setFlowData(flowDataResult);
      } catch (flowError) {
        // Flow might not exist yet, that's okay
        setFlowData({ nodes: [], edges: [] });
      }
    } catch (error) {
      showMessage('error', 'Failed to load repository data');
    }
  }, [selectedRepoName, showMessage]);

  const loadGraphData = useCallback(async () => {
    if (!selectedRepoName) return;
    try {
      const graphDataResult = await apiService.getGraph(selectedRepoName);
      setGraphData(graphDataResult);
    } catch (error) {
      showMessage('error', 'Failed to load graph data');
      setGraphData(null);
    }
  }, [selectedRepoName, showMessage]);

  useEffect(() => {
    loadRepositoryList();
  }, [loadRepositoryList]);

  useEffect(() => {
    if (selectedRepoName) {
      loadRepositoryData();
    }
  }, [selectedRepoName, loadRepositoryData]);

  const createRepository = useCallback(async (name: string) => {
    try {
      const metadata: RepositorySetMetadata = { name, concepts: [], inferences: [] };
      await apiService.createRepositorySet(metadata);
      await loadRepositoryList();
      setSelectedRepoName(name);
      showMessage('success', `Created ${name}`);
    } catch (error) {
      showMessage('error', 'Failed to create repository');
    }
  }, [loadRepositoryList, showMessage]);

  const deleteRepository = useCallback(async () => {
    if (!selectedRepoName || !confirm(`Delete ${selectedRepoName}?`)) return;

    try {
      await apiService.deleteRepositorySet(selectedRepoName);
      await loadRepositoryList();
      setSelectedRepoName('');
      setConcepts([]);
      setInferences([]);
      showMessage('success', 'Repository deleted');
    } catch (error) {
      showMessage('error', 'Failed to delete repository');
    }
  }, [selectedRepoName, loadRepositoryList, showMessage]);

  const addGlobalConceptToRepo: (data: {
    global_concept_id: string;
    reference_data: any;
    reference_axis_names: string[];
    is_ground_concept: boolean;
    is_final_concept: boolean;
    is_invariant: boolean;
  }) => Promise<boolean> = useCallback(async (data) => {
    if (!selectedRepoName) return false;

    try {
      await apiService.addConceptFromGlobal(selectedRepoName, data);
      await loadRepositoryData();
      showMessage('success', 'Concept added to repository');
      return true;
    } catch (error) {
      showMessage('error', 'Failed to add concept to repository');
      return false;
    }
  }, [selectedRepoName, loadRepositoryData, showMessage]);

  const addGlobalInferenceToRepo: (data: {
    global_inference_id: string;
    flow_info: any;
    working_interpretation: any;
    start_without_value: boolean;
    start_without_value_only_once: boolean;
    start_without_function: boolean;
    start_without_function_only_once: boolean;
    start_with_support_reference_only: boolean;
  }) => Promise<boolean> = useCallback(async (data) => {
    if (!selectedRepoName) return false;

    try {
      await apiService.addInferenceFromGlobal(selectedRepoName, data);
      await loadRepositoryData();
      showMessage('success', 'Inference added to repository');
      return true;
    } catch (error) {
      showMessage('error', 'Failed to add inference to repository');
      return false;
    }
  }, [selectedRepoName, loadRepositoryData, showMessage]);

  const removeConceptFromRepo = useCallback(async (conceptId: string) => {
    if (!selectedRepoName || !confirm('Remove this concept from repository?')) return;

    try {
      await apiService.deleteConcept(selectedRepoName, conceptId);
      await loadRepositoryData();
      showMessage('success', 'Concept removed');
    } catch (error) {
      showMessage('error', 'Failed to remove concept');
    }
  }, [selectedRepoName, loadRepositoryData, showMessage]);

  const removeInferenceFromRepo = useCallback(async (inferenceId: string) => {
    if (!selectedRepoName || !confirm('Remove this inference from repository?')) return;

    try {
      await apiService.deleteInference(selectedRepoName, inferenceId);
      await loadRepositoryData();
      showMessage('success', 'Inference removed');
    } catch (error) {
      showMessage('error', 'Failed to remove inference');
    }
  }, [selectedRepoName, loadRepositoryData, showMessage]);

  const saveFlow = useCallback(async (newFlowData: typeof flowData) => {
    if (!selectedRepoName) return;
    
    try {
      await apiService.saveFlow(selectedRepoName, newFlowData);
      setFlowData(newFlowData);
      showMessage('success', 'Flow saved successfully');
    } catch (error) {
      showMessage('error', 'Failed to save flow');
    }
  }, [selectedRepoName, showMessage]);

  return {
    repositories,
    selectedRepoName,
    setSelectedRepoName,
    concepts,
    inferences,
    flowData,
    graphData,
    loadGraphData,
    createRepository,
    deleteRepository,
    addGlobalConceptToRepo,
    addGlobalInferenceToRepo,
    removeConceptFromRepo,
    removeInferenceFromRepo,
    saveFlow,
  };
};

