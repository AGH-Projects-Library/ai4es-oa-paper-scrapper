import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, throwError } from 'rxjs';
import { ResolveDoiRequest, ResolveDoiResponse } from '../models/resolve-doi.model';
import { ApiErrorResponse, ApiRequestError } from '../models/api-error.model';

@Injectable({
  providedIn: 'root',
})
export class Doi {
  private readonly http = inject(HttpClient);

  private readonly baseUrl = 'http://localhost:8000/api';

  resolveDoi(payload: ResolveDoiRequest): Observable<ResolveDoiResponse> {
    return this.http
      .post<ResolveDoiResponse>(`${this.baseUrl}/resolve-doi/`, payload)
      .pipe(catchError((error) => this.handleHttpError(error)));
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