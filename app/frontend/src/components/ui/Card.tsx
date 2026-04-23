import { cn } from '../../utils/cn'

interface CardProps {
  children: React.ReactNode
  className?: string
  onClick?: () => void
}

export const Card = ({ children, className, onClick }: CardProps) => {
  return (
    <div
      className={cn(
        'rounded-xl border border-gray-200 bg-white shadow-sm hover:shadow-md transition-shadow',
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

export const CardHeader = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={cn('border-b border-gray-100 p-4', className)}>{children}</div>
)

export const CardContent = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={cn('p-4', className)}>{children}</div>
)

export const CardFooter = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={cn('border-t border-gray-100 bg-gray-50 p-4', className)}>{children}</div>
)
