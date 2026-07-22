import { Outlet } from "react-router-dom"
import Sidebar from "./components/Sidebar"
import { ToastProvider } from "./components/Toast"
import { MemoryFormProvider } from "./components/MemoryForm"

export default function App() {
  return (
    <ToastProvider>
      <MemoryFormProvider>
        <div className="flex h-screen bg-canvas text-ink-2">
          <Sidebar />
          <main className="flex-1 min-w-0 flex flex-col overflow-hidden">
            <Outlet />
          </main>
        </div>
      </MemoryFormProvider>
    </ToastProvider>
  )
}
