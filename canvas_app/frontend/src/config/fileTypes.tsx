/**
 * File type configuration for the editor.
 * 
 * This module provides centralized configuration for all supported file types,
 * including icons, colors, and capabilities.
 */

import React from 'react';
import {
  FileText,
  File,
  Code,
  FileCode,
  FileJson,
  FileType,
  Hash,
  Database,
  MessageSquare,
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

export type FileCategory = 'normcode' | 'code' | 'data' | 'doc' | 'config' | 'other';

export interface FileTypeConfig {
  extension: string;
  formatName: string;
  displayName: string;
  category: FileCategory;
  icon: React.ComponentType<{ className?: string }>;
  iconColor: string;
  supportsParsing: boolean;
  supportsLineEdit: boolean;
  supportsPreview: boolean;
}

export interface ConceptTypeBadge {
  bg: string;
  text: string;
  label: string;
}

export interface InferenceMarkerBadge {
  bg: string;
  text: string;
}

// =============================================================================
// File Type Registry
// =============================================================================

export const FILE_TYPES: Record<string, FileTypeConfig> = {
  // NormCode family
  ncd: {
    extension: '.ncd',
    formatName: 'ncd',
    displayName: 'NormCode Draft',
    category: 'normcode',
    icon: FileCode,
    iconColor: 'text-blue-500',
    supportsParsing: true,
    supportsLineEdit: true,
    supportsPreview: true,
  },
  ncn: {
    extension: '.ncn',
    formatName: 'ncn',
    displayName: 'NormCode Natural',
    category: 'normcode',
    icon: FileText,
    iconColor: 'text-green-500',
    supportsParsing: true,
    supportsLineEdit: true,
    supportsPreview: true,
  },
  ncdn: {
    extension: '.ncdn',
    formatName: 'ncdn',
    displayName: 'NormCode Draft+Natural',
    category: 'normcode',
    icon: Code,
    iconColor: 'text-purple-500',
    supportsParsing: true,
    supportsLineEdit: true,
    supportsPreview: true,
  },
  ncds: {
    extension: '.ncds',
    formatName: 'ncds',
    displayName: 'NormCode Draft Script',
    category: 'normcode',
    icon: Code,
    iconColor: 'text-indigo-500',
    supportsParsing: true,
    supportsLineEdit: true,
    supportsPreview: true,
  },
  nci: {
    extension: '.nci.json',
    formatName: 'nci',
    displayName: 'NormCode Inference',
    category: 'normcode',
    icon: FileJson,
    iconColor: 'text-red-500',
    supportsParsing: true,
    supportsLineEdit: false,
    supportsPreview: false,
  },
  'nc-json': {
    extension: '.nc.json',
    formatName: 'nc-json',
    displayName: 'NormCode JSON',
    category: 'normcode',
    icon: FileJson,
    iconColor: 'text-orange-500',
    supportsParsing: true,
    supportsLineEdit: false,
    supportsPreview: false,
  },
  concept: {
    extension: '.concept.json',
    formatName: 'concept',
    displayName: 'Concept Definition',
    category: 'normcode',
    icon: Database,
    iconColor: 'text-cyan-500',
    supportsParsing: true,
    supportsLineEdit: false,
    supportsPreview: false,
  },
  inference: {
    extension: '.inference.json',
    formatName: 'inference',
    displayName: 'Inference Definition',
    category: 'normcode',
    icon: Hash,
    iconColor: 'text-pink-500',
    supportsParsing: true,
    supportsLineEdit: false,
    supportsPreview: false,
  },

  // Data formats
  json: {
    extension: '.json',
    formatName: 'json',
    displayName: 'JSON',
    category: 'data',
    icon: FileJson,
    iconColor: 'text-yellow-500',
    supportsParsing: true,
    supportsLineEdit: false,
    supportsPreview: false,
  },
  yaml: {
    extension: '.yaml',
    formatName: 'yaml',
    displayName: 'YAML',
    category: 'data',
    icon: File,
    iconColor: 'text-amber-500',
    supportsParsing: false,
    supportsLineEdit: false,
    supportsPreview: false,
  },
  toml: {
    extension: '.toml',
    formatName: 'toml',
    displayName: 'TOML',
    category: 'data',
    icon: File,
    iconColor: 'text-orange-400',
    supportsParsing: false,
    supportsLineEdit: false,
    supportsPreview: false,
  },

  // Code formats
  python: {
    extension: '.py',
    formatName: 'python',
    displayName: 'Python',
    category: 'code',
    icon: FileType,
    iconColor: 'text-blue-400',
    supportsParsing: false,
    supportsLineEdit: false,
    supportsPreview: false,
  },

  // Documentation
  markdown: {
    extension: '.md',
    formatName: 'markdown',
    displayName: 'Markdown',
    category: 'doc',
    icon: FileText,
    iconColor: 'text-gray-600',
    supportsParsing: false,
    supportsLineEdit: false,
    supportsPreview: true,
  },
  text: {
    extension: '.txt',
    formatName: 'text',
    displayName: 'Plain Text',
    category: 'doc',
    icon: FileText,
    iconColor: 'text-gray-400',
    supportsParsing: false,
    supportsLineEdit: false,
    supportsPreview: false,
  },
};

// =============================================================================
// NormCode Concept Badges
// =============================================================================

export const CONCEPT_TYPE_BADGES: Record<string, ConceptTypeBadge> = {
  object: { bg: 'bg-blue-100', text: 'text-blue-700', label: '{}' },
  proposition: { bg: 'bg-purple-100', text: 'text-purple-700', label: '<>' },
  relation: { bg: 'bg-green-100', text: 'text-green-700', label: '[]' },
  subject: { bg: 'bg-pink-100', text: 'text-pink-700', label: ':S:' },
  imperative: { bg: 'bg-orange-100', text: 'text-orange-700', label: '::()' },
  judgement: { bg: 'bg-red-100', text: 'text-red-700', label: '::<>' },
  operator: { bg: 'bg-cyan-100', text: 'text-cyan-700', label: 'OP' },
  informal: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: '⚠' },
  comment: { bg: 'bg-gray-100', text: 'text-gray-500', label: '//' },
};

export const INFERENCE_MARKER_BADGES: Record<string, InferenceMarkerBadge> = {
  ':<:': { bg: 'bg-emerald-100', text: 'text-emerald-700' },
  ':>:': { bg: 'bg-teal-100', text: 'text-teal-700' },
  '<=': { bg: 'bg-amber-100', text: 'text-amber-700' },
  '<-': { bg: 'bg-sky-100', text: 'text-sky-700' },
  '<*': { bg: 'bg-violet-100', text: 'text-violet-700' },
};

export const TYPE_ICONS: Record<string, { icon: React.ComponentType<{ className?: string }>; label: string }> = {
  main: { icon: Code, label: 'Main' },
  comment: { icon: MessageSquare, label: 'Comment' },
  inline_comment: { icon: MessageSquare, label: 'Inline' },
};

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get file type configuration by format name.
 */
export function getFileTypeConfig(formatName: string): FileTypeConfig | undefined {
  return FILE_TYPES[formatName];
}

/**
 * Check if a format is in the NormCode family.
 */
export function isNormCodeFormat(formatName: string): boolean {
  const config = FILE_TYPES[formatName];
  return config?.category === 'normcode';
}

/**
 * Check if a format supports line-by-line editing.
 */
export function supportsLineEdit(formatName: string): boolean {
  const config = FILE_TYPES[formatName];
  return config?.supportsLineEdit ?? false;
}

/**
 * Check if a format supports parsing.
 */
export function supportsParsing(formatName: string): boolean {
  const config = FILE_TYPES[formatName];
  return config?.supportsParsing ?? false;
}

/**
 * Get all supported file extensions.
 */
export function getSupportedExtensions(): string[] {
  return Object.values(FILE_TYPES).map(config => config.extension);
}

/**
 * Get format icon component with proper styling.
 */
export function getFormatIcon(formatName: string): React.ReactNode {
  const config = FILE_TYPES[formatName] || FILE_TYPES.text;
  const Icon = config.icon;
  return <Icon className={`w-4 h-4 ${config.iconColor}`} />;
}

/**
 * Get formats that support line-by-line editing.
 */
export function getLineEditFormats(): string[] {
  return Object.entries(FILE_TYPES)
    .filter(([, config]) => config.supportsLineEdit)
    .map(([name]) => name);
}

/**
 * Get NormCode family formats.
 */
export function getNormCodeFormats(): string[] {
  return Object.entries(FILE_TYPES)
    .filter(([, config]) => config.category === 'normcode')
    .map(([name]) => name);
}

