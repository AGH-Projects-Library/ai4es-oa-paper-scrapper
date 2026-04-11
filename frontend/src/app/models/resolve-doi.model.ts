import { ResolvedPaper } from './paper.model';

export interface ResolveDoiRequest {
  doi: string;
}

export interface ResolveDoiSuccessResponse {
  status: 'success';
  paper: ResolvedPaper;
}

export interface ResolveDoiNotFoundResponse {
  status: 'not_found';
  message: string;
}

export type ResolveDoiResponse =
  | ResolveDoiSuccessResponse
  | ResolveDoiNotFoundResponse;