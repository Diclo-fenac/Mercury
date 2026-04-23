import { cn } from '../../utils/cn'

interface AvatarProps {
  src?: string
  alt?: string
  name?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export const Avatar = ({ src, alt, name, size = 'md', className }: AvatarProps) => {
  const sizes = {
    sm: 'h-8 w-8 text-xs',
    md: 'h-10 w-10 text-sm',
    lg: 'h-16 w-16 text-base',
  }

  const initials = name
    ? name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : ''

  return (
    <div className={cn('flex items-center justify-center rounded-full bg-primary-100 text-primary-600 font-medium', sizes[size], className)}>
      {src ? (
        <img src={src} alt={alt} className="h-full w-full rounded-full object-cover" />
      ) : (
        initials
      )}
    </div>
  )
}
