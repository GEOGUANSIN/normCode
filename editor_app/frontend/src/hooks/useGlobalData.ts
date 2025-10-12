import { useState, useEffect, useCallback } from 'react';
import { ConceptEntry, InferenceEntry } from '../types';
import { apiService } from '../services/api';
import { MessageType } from './useMessage';

export const useGlobalData = (showMessage: (type: MessageType, text: string) => void) => {
  const [globalConcepts, setGlobalConcepts] = useState<ConceptEntry[]>([]);
  const [globalInferences, setGlobalInferences] = useState<InferenceEntry[]>([]);

  const loadGlobalData = useCallback(async () => {
    try {
      const [conceptsData, inferencesData] = await Promise.all([
        apiService.getGlobalConcepts(),
        apiService.getGlobalInferences()
      ]);
      setGlobalConcepts(conceptsData);
      setGlobalInferences(inferencesData);
    } catch (error) {
      showMessage('error', 'Failed to load global data');
    }
  }, [showMessage]);

  useEffect(() => {
    loadGlobalData();
  }, [loadGlobalData]);

  const addGlobalConcept = useCallback(async (newConcept: ConceptEntry) => {
    try {
      await apiService.addGlobalConcept(newConcept);
      await loadGlobalData();
      showMessage('success', 'Global concept added');
      return true;
    } catch (error) {
      showMessage('error', 'Failed to add global concept');
      return false;
    }
  }, [loadGlobalData, showMessage]);

  const deleteGlobalConcept = useCallback(async (conceptId: string) => {
    if (!confirm('Delete this global concept?')) return;

    try {
      await apiService.deleteGlobalConcept(conceptId);
      await loadGlobalData();
      showMessage('success', 'Global concept deleted');
    } catch (error) {
      showMessage('error', 'Failed to delete global concept');
    }
  }, [loadGlobalData, showMessage]);

  const addGlobalInference = useCallback(async (newInference: InferenceEntry) => {
    try {
      await apiService.addGlobalInference(newInference);
      await loadGlobalData();
      showMessage('success', 'Global inference added');
      return true;
    } catch (error) {
      showMessage('error', 'Failed to add global inference');
      return false;
    }
  }, [loadGlobalData, showMessage]);

  const deleteGlobalInference = useCallback(async (inferenceId: string) => {
    if (!confirm('Delete this global inference?')) return;

    try {
      await apiService.deleteGlobalInference(inferenceId);
      await loadGlobalData();
      showMessage('success', 'Global inference deleted');
    } catch (error) {
      showMessage('error', 'Failed to delete global inference');
    }
  }, [loadGlobalData, showMessage]);

  return {
    globalConcepts,
    globalInferences,
    addGlobalConcept,
    deleteGlobalConcept,
    addGlobalInference,
    deleteGlobalInference,
  };
};

