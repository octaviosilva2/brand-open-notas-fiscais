/** Extrai a mensagem de erro de uma resposta do backend ({code,message,details})
 * de forma robusta, com fallback para mensagem genérica. */

import { ApiError } from '../../api/http';

export function backendMessage(err: unknown, fallback = 'Ocorreu um erro. Tente novamente.'): string {
  if (err instanceof ApiError) {
    const body = err.body as { message?: string; detail?: string } | null;
    if (body?.message) return body.message;
    if (body?.detail) return body.detail;
    if (err.status === 409) return 'Conflito: registro já existe ou está em uso.';
  }
  return fallback;
}
