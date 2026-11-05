import { AppShell } from "@/components/AppShell";
import { DocumentDetailPage } from "@/features/documents/DocumentDetailPage";
import { DocumentListPage } from "@/features/documents/DocumentListPage";

/** Route table is configuration, not a component (see eslint.config.js). */
export const routes = [
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <DocumentListPage /> },
      { path: "documents/:id", element: <DocumentDetailPage /> },
    ],
  },
];
