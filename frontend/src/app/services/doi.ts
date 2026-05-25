import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, throwError } from 'rxjs';
import { ResolveDoiRequest, ResolveDoiResponse } from '../models/resolve-doi.model';
import { ApiErrorResponse, ApiRequestError } from '../models/api-error.model';
import { PaperTableMeta, PaperTableData, PaperImage } from '../models/paper.model';

export interface FetchSectionsRequest {
  doi: string;
  sections: string[];
}

export interface FetchSectionsResponse {
  status: 'success';
  sections: Array<{ id: string; name: string; content: string }>;
}

export interface GetTablesResponse {
  status: 'success';
  tables: PaperTableMeta[];
}

export interface GetTableDetailResponse extends PaperTableData {
  status: 'success';
}

export interface GetImagesResponse {
  status: 'success';
  images: PaperImage[];
}

@Injectable({
  providedIn: 'root',
})
export class Doi {
  private readonly http = inject(HttpClient);

  private readonly baseUrl = 'http://localhost:8000';

  resolveDoi(payload: ResolveDoiRequest): Observable<ResolveDoiResponse> {
    return this.http
      .post<ResolveDoiResponse>(`${this.baseUrl}/resolve-doi/`, payload)
      .pipe(catchError((error) => this.handleHttpError(error)));
  }

    fetchSections(payload: FetchSectionsRequest): Observable<FetchSectionsResponse> {
    return this.http
      .post<FetchSectionsResponse>(`${this.baseUrl}/fetch-sections/`, payload)
      .pipe(catchError((error) => this.handleHttpError(error)));
  }

  getTables(paperId: number): Observable<GetTablesResponse> {
    return this.http
      .get<GetTablesResponse>(`${this.baseUrl}/papers/${paperId}/tables/`)
      .pipe(catchError((error) => this.handleHttpError(error)));
  }

  getTableDetail(paperId: number, globalIndex: number): Observable<GetTableDetailResponse> {
    return this.http
      .get<GetTableDetailResponse>(`${this.baseUrl}/papers/${paperId}/tables/${globalIndex}/`)
      .pipe(catchError((error) => this.handleHttpError(error)));
  }

  getImages(paperId: number): Observable<GetImagesResponse> {
    return this.http
      .get<GetImagesResponse>(`${this.baseUrl}/papers/${paperId}/images/`)
      .pipe(catchError((error) => this.handleHttpError(error)));
  }

  imageUrl(paperId: number, idx: number): string {
    return `${this.baseUrl}/papers/${paperId}/images/${idx}/`;
  }

  private handleHttpError(error: HttpErrorResponse) {
    const payload = error.error as Partial<ApiErrorResponse> | null;

    const apiError = new ApiRequestError({
      message:
        payload?.error?.message ||
        this.getDefaultMessage(error.status) ||
        'Something went wrong while contacting the server.',
      code: payload?.error?.code || 'HTTP_ERROR',
      status: error.status,
      details: payload?.error?.details ?? error.error,
    });

    return throwError(() => apiError);
  }

  private getDefaultMessage(status: number): string {
    switch (status) {
      case 0:
        return 'Could not connect to the server.';
      case 400:
        return 'The request was invalid.';
      case 404:
        return 'The requested endpoint was not found.';
      case 405:
        return 'This endpoint does not allow that HTTP method.';
      case 500:
        return 'The server returned an internal error.';
      default:
        return 'Unexpected server error.';
    }
  }
}