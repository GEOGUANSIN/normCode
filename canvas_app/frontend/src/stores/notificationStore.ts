/**
 * Notification/Toast state management
 * Provides prominent alerts for errors, warnings, and info messages
 */

import { create } from 'zustand';

export type NotificationType = 'info' | 'success' | 'warning' | 'error';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number; // ms, 0 = persistent
  timestamp: Date;
  dismissible?: boolean;
}

interface NotificationState {
  notifications: Notification[];
  
  // Actions
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => string;
  removeNotification: (id: string) => void;
  clearAll: () => void;
  
  // Convenience methods
  showInfo: (title: string, message?: string, duration?: number) => string;
  showSuccess: (title: string, message?: string, duration?: number) => string;
  showWarning: (title: string, message?: string, duration?: number) => string;
  showError: (title: string, message?: string, duration?: number) => string;
}

let notificationIdCounter = 0;

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],

  addNotification: (notification) => {
    const id = `notification-${++notificationIdCounter}-${Date.now()}`;
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: new Date(),
      dismissible: notification.dismissible ?? true,
      duration: notification.duration ?? (notification.type === 'error' ? 0 : 5000), // Errors persist by default
    };

    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }));

    // Auto-dismiss if duration is set
    if (newNotification.duration && newNotification.duration > 0) {
      setTimeout(() => {
        get().removeNotification(id);
      }, newNotification.duration);
    }

    return id;
  },

  removeNotification: (id) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },

  clearAll: () => {
    set({ notifications: [] });
  },

  // Convenience methods
  showInfo: (title, message, duration = 4000) => {
    return get().addNotification({ type: 'info', title, message, duration });
  },

  showSuccess: (title, message, duration = 3000) => {
    return get().addNotification({ type: 'success', title, message, duration });
  },

  showWarning: (title, message, duration = 6000) => {
    return get().addNotification({ type: 'warning', title, message, duration });
  },

  showError: (title, message, duration = 0) => {
    // Errors persist until dismissed by default
    return get().addNotification({ type: 'error', title, message, duration });
  },
}));

