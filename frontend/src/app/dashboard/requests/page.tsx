"use client";

import { useState, useEffect, useMemo, useCallback, useTransition } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { vaultApi } from "@/lib/api/vault";
import { 
  FileSearch, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Loader2, 
  File, 
  Brain,
  Bell,
  AlertTriangle,
  Info,
  X,
  RefreshCw
} from "lucide-react";
import { HoloCard } from "@/components/ui/holo-card";
import {
  getNotifications,
  markNotificationAsRead,
  deleteNotification as deleteNotif,
  markAllAsRead as markAllRead,
  clearAllNotifications as clearAll,
  getUnreadCount,
  type Notification,
} from "@/lib/utils/notifications";

interface PendingFile {
  id: string | number;
  filename: string;
  size: number;
  uploaded_at: string;
  clearance_level: string;
  status: "pending" | "processing" | "completed" | "failed";
}

type TabType = "requests" | "alerts";

export default function RequestsPage() {
  const [activeTab, setActiveTab] = useState<TabType>("requests");
  const [isPending, startTransition] = useTransition();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [recentQueries, setRecentQueries] = useState<Array<{
    query: string;
    timestamp: Date;
    status: "completed" | "pending" | "failed";
  }>>([]);
  const queryClient = useQueryClient();

  // Optimized tab switching with transition
  const handleTabChange = useCallback((tab: TabType) => {
    startTransition(() => {
      setActiveTab(tab);
    });
  }, []);

  // Fetch files from vault
  const { data: filesData, isLoading: filesLoading, refetch: refetchFiles } = useQuery({
    queryKey: ["vault-files"],
    queryFn: async () => {
      try {
        return await vaultApi.listFiles();
      } catch (err) {
        console.error("Failed to fetch files:", err);
        return { files: [], total: 0 };
      }
    },
    retry: (failureCount, error: any) => {
      if (error?.code === 'ERR_NETWORK') {
        return false;
      }
      return failureCount < 3;
    },
    retryDelay: 1000,
  });

  // Load notifications from localStorage - only once on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const loadedNotifications = getNotifications();
      setNotifications(loadedNotifications);

      // Load recent queries
      const queriesStored = localStorage.getItem("recent-queries");
      if (queriesStored) {
        try {
          const parsed = JSON.parse(queriesStored);
          setRecentQueries(parsed.map((q: any) => ({
            ...q,
            timestamp: new Date(q.timestamp),
          })));
        } catch (e) {
          console.error("Failed to parse recent queries:", e);
        }
      }
    }
    // Removed filesData dependency to prevent unnecessary re-runs
  }, []);

  // Refresh notifications periodically
  useEffect(() => {
    const interval = setInterval(() => {
      const loadedNotifications = getNotifications();
      setNotifications(loadedNotifications);
    }, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, []);

  // Memoized notification handlers
  const markAsRead = useCallback((id: string) => {
    markNotificationAsRead(id);
    const updated = getNotifications();
    setNotifications(updated);
  }, []);

  const deleteNotification = useCallback((id: string) => {
    deleteNotif(id);
    const updated = getNotifications();
    setNotifications(updated);
  }, []);

  const handleMarkAllAsRead = useCallback(() => {
    markAllRead();
    const updated = getNotifications();
    setNotifications(updated);
  }, []);

  const handleClearAllNotifications = useCallback(() => {
    clearAll();
    setNotifications([]);
  }, []);

  // Memoized expensive computations
  const pendingFiles = useMemo((): PendingFile[] => {
    if (!filesData?.files) return [];
    
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
    return filesData.files
      .filter((file) => {
        const uploaded = new Date(file.uploaded_at);
        return uploaded > oneHourAgo;
      })
      .map((file) => ({
        ...file,
        status: "processing" as const,
      }));
  }, [filesData?.files]);

  const pendingQueries = useMemo(() => 
    recentQueries.filter((q) => q.status === "pending"),
    [recentQueries]
  );

  const unreadCount = useMemo(() => getUnreadCount(), [notifications]);

  // Memoized utility functions
  const formatTimeAgo = useCallback((date: Date | string) => {
    const now = new Date();
    const past = typeof date === "string" ? new Date(date) : date;
    const diffMs = now.getTime() - past.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    
    if (diffMinutes < 1) return "Just now";
    if (diffMinutes < 60) return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    return `${Math.floor(diffHours / 24)} day${Math.floor(diffHours / 24) > 1 ? 's' : ''} ago`;
  }, []);

  const formatFileSize = useCallback((bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-5 h-5 text-cyber-green" />;
      case "failed":
        return <XCircle className="w-5 h-5 text-red-500" />;
      case "processing":
      case "pending":
        return <Loader2 className="w-5 h-5 text-cyber-cyan animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-slate-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "border-cyber-green/50 bg-cyber-green/10";
      case "failed":
        return "border-red-500/50 bg-red-500/10";
      case "processing":
      case "pending":
        return "border-cyber-cyan/50 bg-cyber-cyan/10";
      default:
        return "border-slate-500/50 bg-slate-500/10";
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case "success":
        return <CheckCircle className="w-5 h-5 text-cyber-green" />;
      case "error":
        return <XCircle className="w-5 h-5 text-red-500" />;
      case "warning":
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      default:
        return <Info className="w-5 h-5 text-cyber-cyan" />;
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case "success":
        return "border-cyber-green/50 bg-cyber-green/10";
      case "error":
        return "border-red-500/50 bg-red-500/10";
      case "warning":
        return "border-yellow-500/50 bg-yellow-500/10";
      default:
        return "border-cyber-cyan/50 bg-cyber-cyan/10";
    }
  };

  return (
    <div className="p-8 space-y-6 h-full flex flex-col">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-display uppercase tracking-wider text-white mb-2">
            REQUESTS & ALERTS
          </h1>
          <p className="text-slate-500 text-lg">
            Monitor file processing jobs, investigation queries, and system notifications
          </p>
        </div>
        <button
          onClick={() => refetchFiles()}
          className="px-4 py-2 bg-glass-medium border border-glass-border rounded-lg text-slate-400 hover:text-white hover:border-cyber-cyan/50 transition-all flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-glass-border">
        <button
          onClick={() => handleTabChange("requests")}
          disabled={isPending}
          className={`px-6 py-3 font-medium transition-all relative ${
            activeTab === "requests"
              ? "text-cyber-cyan border-b-2 border-cyber-cyan"
              : "text-slate-500 hover:text-slate-300"
          } ${isPending ? "opacity-50 cursor-wait" : ""}`}
        >
          <div className="flex items-center gap-2">
            <FileSearch className="w-5 h-5" />
            <span>Pending Requests</span>
            {pendingFiles.length > 0 || pendingQueries.length > 0 ? (
              <span className="px-2 py-0.5 bg-cyber-cyan/20 text-cyber-cyan text-xs rounded-full">
                {pendingFiles.length + pendingQueries.length}
              </span>
            ) : null}
          </div>
        </button>
        <button
          onClick={() => handleTabChange("alerts")}
          disabled={isPending}
          className={`px-6 py-3 font-medium transition-all relative ${
            activeTab === "alerts"
              ? "text-cyber-cyan border-b-2 border-cyber-cyan"
              : "text-slate-500 hover:text-slate-300"
          } ${isPending ? "opacity-50 cursor-wait" : ""}`}
        >
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            <span>Alerts & Notifications</span>
            {unreadCount > 0 && (
              <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs rounded-full">
                {unreadCount}
              </span>
            )}
          </div>
        </button>
      </div>

      {/* Tab Content - Using CSS visibility instead of conditional rendering for better performance */}
      <div className="flex-1 overflow-y-auto relative">
        {/* Requests Tab */}
        <div 
          className={`absolute inset-0 overflow-y-auto transition-opacity duration-200 ${
            activeTab === "requests" ? "opacity-100 z-10" : "opacity-0 z-0 pointer-events-none"
          }`}
        >
          <div className="space-y-8">
            {/* Pending Files Section */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <File className="w-6 h-6 text-cyber-cyan" />
                <h2 className="text-xl font-semibold text-white">File Processing Queue</h2>
              </div>

              {filesLoading ? (
                <div className="text-slate-500">Loading files...</div>
              ) : pendingFiles.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {pendingFiles.map((file) => (
                    <HoloCard key={file.id}>
                      <div className={`p-4 rounded-lg border ${getStatusColor(file.status)}`}>
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-2 flex-1 min-w-0">
                            <File className="w-5 h-5 text-cyber-cyan flex-shrink-0" />
                            <span className="text-sm font-medium text-white truncate">
                              {file.filename}
                            </span>
                          </div>
                          {getStatusIcon(file.status)}
                        </div>
                        <div className="space-y-1 text-xs text-slate-400">
                          <div>Size: {formatFileSize(file.size)}</div>
                          <div>Uploaded: {formatTimeAgo(file.uploaded_at)}</div>
                          <div>Clearance: {file.clearance_level}</div>
                        </div>
                        <div className="mt-3 text-xs text-cyber-cyan">
                          {file.status === "processing" && "Processing for GraphRAG ingestion..."}
                          {file.status === "pending" && "Queued for processing..."}
                        </div>
                      </div>
                    </HoloCard>
                  ))}
                </div>
              ) : (
                <div className="text-slate-500 text-center py-8 bg-glass-light backdrop-blur-md border border-glass-border rounded-xl">
                  No files currently processing
                </div>
              )}
            </div>

            {/* Pending Queries Section */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Brain className="w-6 h-6 text-cyber-purple" />
                <h2 className="text-xl font-semibold text-white">Investigation Queries</h2>
              </div>

              {pendingQueries.length > 0 ? (
                <div className="space-y-3">
                  {pendingQueries.map((query, idx) => (
                    <HoloCard key={idx}>
                      <div className={`p-4 rounded-lg border ${getStatusColor(query.status)}`}>
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2 flex-1">
                            <Brain className="w-5 h-5 text-cyber-purple flex-shrink-0" />
                            <span className="text-sm text-white">{query.query}</span>
                          </div>
                          {getStatusIcon(query.status)}
                        </div>
                        <div className="text-xs text-slate-400 mt-2">
                          Started: {formatTimeAgo(query.timestamp)}
                        </div>
                      </div>
                    </HoloCard>
                  ))}
                </div>
              ) : (
                <div className="text-slate-500 text-center py-8 bg-glass-light backdrop-blur-md border border-glass-border rounded-xl">
                  No pending investigation queries
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Alerts Tab */}
        <div 
          className={`absolute inset-0 overflow-y-auto transition-opacity duration-200 ${
            activeTab === "alerts" ? "opacity-100 z-10" : "opacity-0 z-0 pointer-events-none"
          }`}
        >
          <div className="space-y-4">
            {/* Alerts & Notifications Section */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bell className="w-6 h-6 text-cyber-purple" />
                <h2 className="text-xl font-semibold text-white">System Notifications</h2>
              </div>
              <div className="flex gap-2">
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllAsRead}
                    className="px-3 py-1.5 text-xs bg-glass-medium border border-glass-border rounded-lg text-slate-400 hover:text-white hover:border-cyber-cyan/50 transition-all"
                  >
                    Mark all read
                  </button>
                )}
                {notifications.length > 0 && (
                  <button
                    onClick={handleClearAllNotifications}
                    className="px-3 py-1.5 text-xs bg-glass-medium border border-glass-border rounded-lg text-slate-400 hover:text-white hover:border-red-500/50 transition-all"
                  >
                    Clear all
                  </button>
                )}
              </div>
            </div>

            {notifications.length > 0 ? (
              <div className="space-y-3">
                {notifications.map((notification) => (
                  <HoloCard key={notification.id}>
                    <div className={`p-4 rounded-lg border ${getNotificationColor(notification.type)} ${!notification.read ? 'ring-2 ring-cyber-cyan/30' : ''}`}>
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 mt-0.5">
                          {getNotificationIcon(notification.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2 mb-1">
                            <h3 className="text-sm font-semibold text-white">
                              {notification.title}
                            </h3>
                            <div className="flex items-center gap-2">
                              {!notification.read && (
                                <span className="w-2 h-2 bg-cyber-cyan rounded-full"></span>
                              )}
                              <button
                                onClick={() => deleteNotification(notification.id)}
                                className="text-slate-500 hover:text-white transition-colors"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                          <p className="text-sm text-slate-300 mb-2">
                            {notification.message}
                          </p>
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-slate-500">
                              {formatTimeAgo(notification.timestamp)}
                            </span>
                            <div className="flex gap-2">
                              {!notification.read && (
                                <button
                                  onClick={() => markAsRead(notification.id)}
                                  className="text-xs text-cyber-cyan hover:text-cyber-cyan/70 transition-colors"
                                >
                                  Mark as read
                                </button>
                              )}
                              {notification.actionUrl && (
                                <a
                                  href={notification.actionUrl}
                                  className="text-xs text-cyber-cyan hover:text-cyber-cyan/70 transition-colors"
                                >
                                  View →
                                </a>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </HoloCard>
                ))}
              </div>
            ) : (
              <div className="text-slate-500 text-center py-12 bg-glass-light backdrop-blur-md border border-glass-border rounded-xl">
                <Bell className="w-12 h-12 mx-auto mb-4 text-slate-700" />
                <p>No notifications</p>
                <p className="text-xs mt-2">You'll see alerts and system updates here</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Info Footer */}
      <div className="mt-auto pt-4 border-t border-glass-border">
        <div className="text-xs text-slate-500 space-y-1">
          {activeTab === "requests" ? (
            <>
              <p>• Files are automatically processed for GraphRAG ingestion after upload</p>
              <p>• Recent queries are cached locally for quick reference</p>
              <p>• Processing status updates in real-time</p>
            </>
          ) : (
            <>
              <p>• Notifications are generated automatically from system events</p>
              <p>• Click on notification actions to navigate to relevant pages</p>
              <p>• Unread notifications are highlighted with a blue indicator</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
