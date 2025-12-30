/**
 * Notification Management Utility
 * Handles creating, storing, and managing system notifications
 */

export interface Notification {
  id: string;
  type: "info" | "success" | "warning" | "error";
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  actionUrl?: string;
}

const NOTIFICATIONS_STORAGE_KEY = "notifications";
const MAX_NOTIFICATIONS = 50;

/**
 * Generate a unique notification ID
 */
function generateNotificationId(): string {
  return `notif-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Get all notifications from localStorage
 */
export function getNotifications(): Notification[] {
  if (typeof window === "undefined") return [];
  
  try {
    const stored = localStorage.getItem(NOTIFICATIONS_STORAGE_KEY);
    if (!stored) return [];
    
    const parsed = JSON.parse(stored);
    return parsed.map((n: any) => ({
      ...n,
      timestamp: new Date(n.timestamp),
    }));
  } catch (e) {
    console.error("Failed to parse notifications:", e);
    return [];
  }
}

/**
 * Save notifications to localStorage
 */
function saveNotifications(notifications: Notification[]): void {
  if (typeof window === "undefined") return;
  
  try {
    // Keep only the most recent notifications
    const limited = notifications
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, MAX_NOTIFICATIONS);
    
    localStorage.setItem(NOTIFICATIONS_STORAGE_KEY, JSON.stringify(limited));
  } catch (e) {
    console.error("Failed to save notifications:", e);
  }
}

/**
 * Create a new notification
 */
export function createNotification(
  type: Notification["type"],
  title: string,
  message: string,
  actionUrl?: string
): Notification {
  const notification: Notification = {
    id: generateNotificationId(),
    type,
    title,
    message,
    timestamp: new Date(),
    read: false,
    actionUrl,
  };

  const existing = getNotifications();
  const updated = [notification, ...existing];
  saveNotifications(updated);

  return notification;
}

/**
 * Mark notification as read
 */
export function markNotificationAsRead(id: string): void {
  const notifications = getNotifications();
  const updated = notifications.map(n => 
    n.id === id ? { ...n, read: true } : n
  );
  saveNotifications(updated);
}

/**
 * Delete notification
 */
export function deleteNotification(id: string): void {
  const notifications = getNotifications();
  const updated = notifications.filter(n => n.id !== id);
  saveNotifications(updated);
}

/**
 * Mark all notifications as read
 */
export function markAllAsRead(): void {
  const notifications = getNotifications();
  const updated = notifications.map(n => ({ ...n, read: true }));
  saveNotifications(updated);
}

/**
 * Clear all notifications
 */
export function clearAllNotifications(): void {
  saveNotifications([]);
}

/**
 * Get unread notification count
 */
export function getUnreadCount(): number {
  return getNotifications().filter(n => !n.read).length;
}

