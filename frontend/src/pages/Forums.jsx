import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import {
  TrendingUp,
  ThumbsUp,
  MessageCircle,
  Clock,
  MapPin,
  AlertCircle,
  Users,
} from "lucide-react";
import { useTranslation } from "../hooks/useTranslation";
import { formatDistanceToNow } from "date-fns";
import "./Forums.css";
import { API_URL as API_BASE_URL } from "../lib/config";

const Forums = () => {
  const { t } = useTranslation();
  const [trendingComplaints, setTrendingComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTrendingComplaints();
  }, []);

  const fetchTrendingComplaints = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/forum/trending?limit=20`
      );
      if (response.data.success) {
        setTrendingComplaints(response.data.complaints || []);
      } else {
        setError(response.data.error || "Failed to load trending complaints");
      }
    } catch (err) {
      setError(
        err.response?.data?.error ||
          err.message ||
          "Failed to fetch trending complaints"
      );
      console.error("Forums error:", err);
    } finally {
      setLoading(false);
    }
  };

  const getUrgencyColor = (urgency) => {
    const colors = {
      urgent: "#f44336",
      high: "#ff9800",
      medium: "#2196f3",
      low: "#4caf50",
    };
    return colors[urgency] || colors.medium;
  };

  const getStatusColor = (status) => {
    const colors = {
      open: "#2196f3",
      in_progress: "#ff9800",
      resolved: "#4caf50",
      escalated: "#f44336",
    };
    return colors[status] || colors.open;
  };

  if (loading) {
    return (
      <div className="forums-loading">
        <div className="loading-spinner"></div>
        <p>{t("loading") || "Loading forums..."}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="forums-error">
        <AlertCircle size={24} />
        <p>{error}</p>
        <button onClick={fetchTrendingComplaints} className="btn btn-primary">
          {t("retry") || "Retry"}
        </button>
      </div>
    );
  }

  return (
    <div className="forums-page">
      <div className="forums-header">
        <div>
          <h1>
            <TrendingUp size={28} />
            {t("forumsTitle") || "Community Forums"}
          </h1>
          <p className="forums-subtitle">
            {t("forumsSubtitle") ||
              "Discover trending complaints and join discussions. Upvote issues that matter to you."}
          </p>
        </div>
        <div className="forums-stats">
          <div className="stat-card">
            <TrendingUp size={20} />
            <div>
              <span className="stat-value">{trendingComplaints.length}</span>
              <span className="stat-label">
                {t("trendingComplaints") || "Trending"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {trendingComplaints.length === 0 ? (
        <div className="forums-empty">
          <Users size={64} />
          <h2>{t("noTrendingComplaints") || "No Trending Complaints Yet"}</h2>
          <p>
            {t("noTrendingComplaintsDesc") ||
              "Be the first to start a discussion! File a complaint to get started."}
          </p>
          <Link to="/" className="btn btn-primary">
            {t("fileComplaint") || "File a Complaint"}
          </Link>
        </div>
      ) : (
        <div className="forums-grid">
          {trendingComplaints.map((complaint) => {
            const location =
              typeof complaint.location === "string"
                ? JSON.parse(complaint.location || "{}")
                : complaint.location || {};

            return (
              <Link
                key={complaint.id}
                to={`/forum/${complaint.id}`}
                className="forum-card"
              >
                <div className="forum-card-header">
                  <div className="complaint-badges">
                    <span
                      className="urgency-badge"
                      style={{
                        backgroundColor: getUrgencyColor(complaint.urgency),
                      }}
                    >
                      {complaint.urgency?.toUpperCase() || "MEDIUM"}
                    </span>
                    <span
                      className="status-badge"
                      style={{
                        backgroundColor: getStatusColor(complaint.status),
                      }}
                    >
                      {complaint.status?.replace("_", " ").toUpperCase() ||
                        "OPEN"}
                    </span>
                  </div>
                  <span className="complaint-id">
                    #{complaint.id.slice(0, 8)}
                  </span>
                </div>

                <div className="forum-card-body">
                  <p className="complaint-description">
                    {complaint.description?.substring(0, 200)}
                    {complaint.description?.length > 200 ? "..." : ""}
                  </p>

                  {location.city || location.state ? (
                    <div className="complaint-location">
                      <MapPin size={14} />
                      <span>
                        {location.city ? `${location.city}, ` : ""}
                        {location.state || ""}
                      </span>
                    </div>
                  ) : null}

                  <div className="complaint-department">
                    <span className="dept-label">
                      {t("department") || "Department"}:
                    </span>
                    <span className="dept-name">
                      {complaint.responsible_department || "N/A"}
                    </span>
                  </div>
                </div>

                <div className="forum-card-footer">
                  <div className="engagement-stats">
                    <div className="stat-item">
                      <ThumbsUp size={16} />
                      <span>{complaint.upvote_count || 0}</span>
                    </div>
                    <div className="stat-item">
                      <MessageCircle size={16} />
                      <span>{complaint.forum_post_count || 0}</span>
                    </div>
                    {complaint.community_priority_boost > 0 && (
                      <div className="stat-item priority">
                        <TrendingUp size={16} />
                        <span>
                          +
                          {(complaint.community_priority_boost * 100).toFixed(
                            0
                          )}
                          %
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="complaint-date">
                    <Clock size={14} />
                    <span>
                      {formatDistanceToNow(new Date(complaint.created_at), {
                        addSuffix: true,
                      })}
                    </span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Forums;
