/**
 * Toast Notification Component
 * Displays prominent notifications for errors, warnings, and info
 */

import { useState } from 'react';
import { 
  X, 
  CheckCircle, 
  AlertTriangle, 
  AlertCircle, 
  Info,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useNotificationStore, Notification, NotificationType } from '../../stores/notificationStore';

const typeConfig: Record<NotificationType, {
  icon: typeof Info;
  bgColor: string;
  borderColor: string;
  iconColor: string;
  titleColor: string;
}> = {
  info: {
    icon: Info,
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    iconColor: 'text-blue-500',
    titleColor: 'text-blue-800',
  },
  success: {
    icon: CheckCircle,
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    iconColor: 'text-green-500',
    titleColor: 'text-green-800',
  },
  warning: {
    icon: AlertTriangle,
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    iconColor: 'text-yellow-500',
    titleColor: 'text-yellow-800',
  },
  error: {
    icon: AlertCircle,
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    iconColor: 'text-red-500',
    titleColor: 'text-red-800',
  },
};

interface ToastItemProps {
  notification: Notification;
  onDismiss: () => void;
}

function ToastItem({ notification, onDismiss }: ToastItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  const config = typeConfig[notification.type];
  const Icon = config.icon;
  
  // Long message handling
  const isLongMessage = notification.message && notification.message.length > 100;
  const displayMessage = isLongMessage && !isExpanded 
    ? notification.message?.substring(0, 100) + '...'
    : notification.message;

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(onDismiss, 200); // Wait for exit animation
  };

  return (
    <div
      className={`
        ${config.bgColor} ${config.borderColor} border
        rounded-lg shadow-lg p-4 max-w-md w-full
        transform transition-all duration-200 ease-out
        ${isExiting ? 'opacity-0 translate-x-4' : 'opacity-100 translate-x-0'}
      `}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 ${config.iconColor} shrink-0 mt-0.5`} />
        
        <div className="flex-1 min-w-0">
          <h4 className={`text-sm font-semibold ${config.titleColor}`}>
            {notification.title}
          </h4>
          
          {notification.message && (
            <div className="mt-1">
              <p className="text-sm text-slate-600 break-words whitespace-pre-wrap">
                {displayMessage}
              </p>
              
              {isLongMessage && (
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="mt-1 text-xs text-slate-500 hover:text-slate-700 flex items-center gap-1"
                >
                  {isExpanded ? (
                    <>
                      <ChevronUp size={12} /> Show less
                    </>
                  ) : (
                    <>
                      <ChevronDown size={12} /> Show more
                    </>
                  )}
                </button>
              )}
            </div>
          )}
        </div>
        
        {notification.dismissible !== false && (
          <button
            onClick={handleDismiss}
            className="p-1 text-slate-400 hover:text-slate-600 rounded transition-colors"
            aria-label="Dismiss"
          >
            <X size={16} />
          </button>
        )}
      </div>
    </div>
  );
}

export function ToastContainer() {
  const notifications = useNotificationStore((s) => s.notifications);
  const removeNotification = useNotificationStore((s) => s.removeNotification);

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div 
      className="fixed top-16 right-4 z-50 flex flex-col gap-2 pointer-events-none"
      aria-live="polite"
    >
      {notifications.map((notification) => (
        <div key={notification.id} className="pointer-events-auto">
          <ToastItem
            notification={notification}
            onDismiss={() => removeNotification(notification.id)}
          />
        </div>
      ))}
    </div>
  );
}

