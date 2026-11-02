import { AppShell } from "@/components/AppShell";
import { DocumentListPage } from "@/features/documents/DocumentListPage";

/** Route table is configuration, not a component (see eslint.config.js). */
export const routes = [
  {
    path: "/",
    element: <AppShell />,
    children: [{ index: true, element: <DocumentListPage /> }],
  },
];
