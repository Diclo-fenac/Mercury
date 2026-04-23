import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { usersApi, UserProfile } from '../api/users'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Avatar } from '../components/ui/Avatar'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { Button } from '../components/ui/Button'

export const Profile = () => {
  const { user, isAuthenticated } = useAuth()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (isAuthenticated() && user?.user_id) {
      const loadProfile = async () => {
        try {
          const data = await usersApi.getProfile(user.user_id)
          setProfile(data.profile)
        } catch (err) {
          console.error('Failed to load profile:', err)
        } finally {
          setLoading(false)
        }
      }
      loadProfile()
    }
  }, [isAuthenticated, user])

  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!profile || !user?.user_id) return

    setSaving(true)
    try {
      await usersApi.updatePreferences(user.user_id, profile.preferences || {})
      alert('Preferences saved successfully!')
    } catch (err) {
      alert('Failed to save preferences')
    } finally {
      setSaving(false)
    }
  }

  if (!isAuthenticated()) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Please login to view your profile</h2>
          <Button onClick={() => window.location.href = '/login'}>Login</Button>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Your Profile</h1>
        <p className="text-gray-500 mt-1">Manage your preferences and activity</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Profile Info */}
        <div className="md:col-span-1">
          <Card className="text-center">
            <CardContent className="p-6">
              <div className="mx-auto mb-4">
                <Avatar name={user?.email || 'User'} size="lg" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">{user?.email}</h2>
              <p className="text-sm text-gray-500 mt-1">User ID: {user?.user_id}</p>
              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Member since</span>
                  <span className="text-gray-900">{profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : 'Unknown'}</span>
                </div>
                <div className="flex justify-between text-sm mt-2">
                  <span className="text-gray-500">Last active</span>
                  <span className="text-gray-900">{profile?.last_active ? new Date(profile.last_active).toLocaleDateString() : 'Unknown'}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Preferences */}
        <div className="md:col-span-2">
          <Card>
            <CardHeader className="border-b border-gray-100">
              <h3 className="font-semibold text-gray-900">Preferences</h3>
            </CardHeader>
            <CardContent className="p-6">
              <form onSubmit={handleSavePreferences} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Categories of Interest</label>
                  <div className="flex flex-wrap gap-2">
                    {['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Toys', 'Food', 'Beauty'].map((category) => (
                      <label key={category} className="inline-flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span className="text-sm text-gray-700">{category}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Communication Preferences</label>
                  <div className="space-y-3">
                    <label className="flex items-center gap-3">
                      <input type="checkbox" defaultChecked className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
                      <span className="text-sm text-gray-700">Email notifications for deals</span>
                    </label>
                    <label className="flex items-center gap-3">
                      <input type="checkbox" defaultChecked className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
                      <span className="text-sm text-gray-700">Push notifications for recommendations</span>
                    </label>
                    <label className="flex items-center gap-3">
                      <input type="checkbox" className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
                      <span className="text-sm text-gray-700">Weekly summary email</span>
                    </label>
                  </div>
                </div>

                <div className="flex justify-end pt-4 border-t border-gray-100">
                  <Button type="submit" isLoading={saving}>Save Preferences</Button>
                </div>
              </form>
            </CardContent>
          </Card>

          <Card className="mt-6">
            <CardHeader className="border-b border-gray-100">
              <h3 className="font-semibold text-gray-900">Activity Summary</h3>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">{profile?.activity_summary?.search_count || 0}</div>
                  <div className="text-sm text-gray-500">Searches</div>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">{profile?.activity_summary?.chat_count || 0}</div>
                  <div className="text-sm text-gray-500">Chats</div>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">{profile?.activity_summary?.image_uploads || 0}</div>
                  <div className="text-sm text-gray-500">Images</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
