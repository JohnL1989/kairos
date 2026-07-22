import React from "react"
import ReactDOM from "react-dom/client"
import { createBrowserRouter, RouterProvider, Navigate } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import App from "./App"
import Overview from "./pages/Overview"
import MemoryExplorer from "./pages/MemoryExplorer"
import Timeline from "./pages/Timeline"
import Categories from "./pages/Categories"
import Pipeline from "./pages/Pipeline"
import Maturity from "./pages/Maturity"
import Health from "./pages/Health"
import "./index.css"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

const router = createBrowserRouter(
  [
    {
      element: <App />,
      children: [
        { index: true, element: <Overview /> },
        { path: "memories", element: <MemoryExplorer /> },
        { path: "timeline", element: <Timeline /> },
        { path: "categories", element: <Categories /> },
        { path: "pipeline", element: <Pipeline /> },
        { path: "maturity", element: <Maturity /> },
        { path: "health", element: <Health /> },
        { path: "*", element: <Navigate to="/memories" replace /> },
      ],
    },
  ],
  { basename: "/console" },
)

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>,
)
