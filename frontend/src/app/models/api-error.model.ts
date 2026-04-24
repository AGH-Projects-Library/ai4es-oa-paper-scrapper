export interface ApiErrorPayload {
  code: string;
  message: string;
  details?: unknown;
}

export interface ApiErrorResponse {
  error: ApiErrorPayload;
}

export class ApiRequestError extends Error {
  readonly code: string;
  readonly status?: number;
  readonly details?: unknown;

  constructor(params: {
    message: string;
    code?: string;
    status?: number;
    details?: unknown;
  }) {
    super(params.message);
    this.name = 'ApiRequestError';
    this.code = params.code ?? 'UNKNOWN_ERROR';
    this.status = params.status;
    this.details = params.details;
  }
}