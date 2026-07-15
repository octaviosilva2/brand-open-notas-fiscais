/** Tipos do domínio de clientes (espelham ClientRead/Create/Update do backend). */

export interface Client {
  id: string;
  document: string;
  document_type: 'CPF' | 'CNPJ';
  name: string;
  municipal_registration: string | null;
  phone: string | null;
  email: string | null;
  zip_code: string | null;
  street: string | null;
  number: string | null;
  complement: string | null;
  neighborhood: string | null;
  ibge_city_code: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ClientCreate {
  document: string;
  name: string;
  municipal_registration?: string | null;
  phone?: string | null;
  email?: string | null;
  zip_code?: string | null;
  street?: string | null;
  number?: string | null;
  complement?: string | null;
  neighborhood?: string | null;
  ibge_city_code?: string | null;
}

export type ClientUpdate = Partial<ClientCreate>;

export interface CnpjData {
  name: string;
  phone: string | null;
  email: string | null;
  zip_code: string | null;
  street: string | null;
  number: string | null;
  complement: string | null;
  neighborhood: string | null;
  ibge_city_code: string | null;
}

export interface Paginated<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
