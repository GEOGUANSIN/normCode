export interface RepositorySet {
  name: string;
  concepts: any[];
  inferences: any[];
}

export interface RepositorySetResponse {
  repository_set_names: string[];
}

export interface RepositorySetDetailResponse {
  repository_set: RepositorySet;
}

export interface RunRepositoryResponse {
  log_file: string;
}

export interface LogContentResponse {
  content: string;
}

export interface ApiError {
  message: string;
  status?: number;
}
