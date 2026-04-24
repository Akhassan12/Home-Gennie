import { Navigate } from 'react-router-dom'
import { useAuth } from '../services/auth'
import { Loader } from 'lucide-react'

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader size={28} className="animate-spin text-primary-400" />
      </div>
    )
  }

  return user ? children : <Navigate to="/login" replace />
}
