/** Definição das rotas: /login público; demais sob RequireAuth + AppLayout. */

import { createBrowserRouter, Navigate } from 'react-router-dom';
import { RequireAuth } from './auth/RequireAuth';
import { AppLayout } from './components/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { ClientsListPage } from './pages/clients/ClientsListPage';
import { ClientCreatePage } from './pages/clients/ClientCreatePage';
import { ClientEditPage } from './pages/clients/ClientEditPage';
import { RecurrenceWizardPage } from './pages/recurrences/RecurrenceWizardPage';
import { RecurrenceEditPage } from './pages/recurrences/RecurrenceEditPage';
import { RecurrencesListPage } from './pages/recurrences/RecurrencesListPage';
import { InvoicesListPage } from './pages/invoices/InvoicesListPage';
import { InvoiceDetailPage } from './pages/invoices/InvoiceDetailPage';

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { index: true, element: <Navigate to="/clientes" replace /> },
          { path: 'clientes', element: <ClientsListPage /> },
          { path: 'clientes/novo', element: <ClientCreatePage /> },
          { path: 'clientes/:id', element: <ClientEditPage /> },
          { path: 'recorrencias', element: <RecurrencesListPage /> },
          { path: 'recorrencias/nova', element: <RecurrenceWizardPage /> },
          { path: 'recorrencias/:id/editar', element: <RecurrenceEditPage /> },
          { path: 'notas', element: <InvoicesListPage /> },
          { path: 'notas/:id', element: <InvoiceDetailPage /> },
        ],
      },
    ],
  },
]);
