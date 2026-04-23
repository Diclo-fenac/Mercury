import { Link, useNavigate } from 'react-router-dom'
import { Button } from '../ui/Button'
import { Avatar } from '../ui/Avatar'
import { useAuth } from '../../hooks/useAuth'
import { useToastStore } from '../ui/Toast'

export const Header = () => {
  const { user, isAuthenticated, logout } = useAuth()
  const { addToast } = useToastStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    addToast('Logged out successfully', 'success')
    navigate('/')
  }

  return (
    <header className="sticky top-0 z-40 w-full border-b border-gray-200 bg-white/80 backdrop-blur">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white font-bold">
            M
          </div>
          <span className="text-xl font-bold text-gray-900">Mercury</span>
        </Link>

        <nav className="hidden md:flex items-center gap-6">
          <Link to="/search" className="text-sm font-medium text-gray-600 hover:text-primary-600">
            Search
          </Link>
          <Link to="/chat" className="text-sm font-medium text-gray-600 hover:text-primary-600">
            Chat
          </Link>
          <Link to="/conversations" className="text-sm font-medium text-gray-600 hover:text-primary-600">
            Conversations
          </Link>
          <Link to="/images" className="text-sm font-medium text-gray-600 hover:text-primary-600">
            Images
          </Link>
        </nav>

        <div className="flex items-center gap-4">
          {isAuthenticated() ? (
            <div className="flex items-center gap-3">
              <Avatar name={user?.email || 'User'} size="sm" />
              <div className="hidden md:block">
                <p className="text-sm font-medium text-gray-900">{user?.email}</p>
                <p className="text-xs text-gray-500">{user?.roles.includes('admin') ? 'Admin' : 'User'}</p>
              </div>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          ) : (
            <Button onClick={() => navigate('/login')}>Login</Button>
          )}
        </div>
      </div>
    </header>
  )
}
