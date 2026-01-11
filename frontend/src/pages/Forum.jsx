import React, { useState, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import {
  ThumbsUp,
  ThumbsDown,
  MessageCircle,
  TrendingUp,
  Users,
  AlertCircle,
  Image as ImageIcon,
  X,
} from "lucide-react";
import { useTranslation } from "../hooks/useTranslation";
import { formatDistanceToNow } from "date-fns";
import { supabase } from "../lib/supabase";
import "./Forum.css";
import { API_URL as API_BASE_URL } from "../lib/config";
const STORAGE_BUCKET = "forum-images";

const Forum = () => {
  const { complaintId } = useParams();
  const { t } = useTranslation();
  const [forumData, setForumData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [voting, setVoting] = useState(false);
  const [posting, setPosting] = useState(false);
  const [newPost, setNewPost] = useState({
    author_name: "",
    author_email: "",
    content: "",
  });
  const [selectedImages, setSelectedImages] = useState([]); // Store File objects
  const [imagePreviews, setImagePreviews] = useState([]);
  const [uploadingImages, setUploadingImages] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (complaintId) {
      fetchForumData();
    }
  }, [complaintId]);

  const fetchForumData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/forum/complaint/${complaintId}`
      );
      if (response.data.success) {
        setForumData(response.data);
      } else {
        setError(response.data.error || "Failed to load forum data");
      }
    } catch (err) {
      setError(
        err.response?.data?.error || err.message || "Failed to fetch forum data"
      );
      console.error("Forum error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleVote = async (voteType) => {
    if (!newPost.author_email) {
      alert(t("forumEmailRequired") || "Please enter your email to vote");
      return;
    }

    setVoting(true);
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/forum/vote`,
        null,
        {
          params: {
            complaint_id: complaintId,
            voter_email: newPost.author_email,
            vote_type: voteType,
          },
        }
      );
      if (response.data.success) {
        // Refresh forum data
        await fetchForumData();
        // Show success message
        const action =
          response.data.action === "added" ? "Vote added" : "Vote removed";
        // Don't show alert for successful votes, just refresh
      } else {
        const errorMsg =
          response.data.error || response.data.message || "Failed to vote";
        alert(errorMsg);
      }
    } catch (err) {
      const errorMsg =
        err.response?.data?.error ||
        err.response?.data?.message ||
        err.message ||
        "Failed to vote. Please check if the forum feature is set up correctly.";
      alert(errorMsg);
      console.error("Vote error:", err);
    } finally {
      setVoting(false);
    }
  };

  const handleImageSelect = (e) => {
    const files = Array.from(e.target.files);
    const maxImages = 5;
    const maxSize = 5 * 1024 * 1024; // 5MB per image

    if (selectedImages.length + files.length > maxImages) {
      alert(t("maxImagesError") || `You can upload up to ${maxImages} images`);
      return;
    }

    files.forEach((file) => {
      if (file.size > maxSize) {
        alert(
          t("imageSizeError") ||
            `Image ${file.name} is too large. Maximum size is 5MB.`
        );
        return;
      }

      if (!file.type.startsWith("image/")) {
        alert(t("imageTypeError") || `File ${file.name} is not an image.`);
        return;
      }

      // Store File object instead of base64
      setSelectedImages((prev) => [...prev, file]);

      // Create preview URL
      const previewUrl = URL.createObjectURL(file);
      setImagePreviews((prev) => [
        ...prev,
        { url: previewUrl, name: file.name, file: file },
      ]);
    });

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const removeImage = (index) => {
    // Revoke object URL to free memory
    const preview = imagePreviews[index];
    if (preview && preview.url && preview.url.startsWith("blob:")) {
      URL.revokeObjectURL(preview.url);
    }
    setSelectedImages((prev) => prev.filter((_, i) => i !== index));
    setImagePreviews((prev) => prev.filter((_, i) => i !== index));
  };

  const uploadImagesToStorage = async (files) => {
    /**
     * Upload images to Supabase Storage and return public URLs.
     */
    const uploadedUrls = [];

    for (const file of files) {
      try {
        // Generate unique filename
        const fileExt = file.name.split(".").pop();
        const fileName = `${Date.now()}-${Math.random()
          .toString(36)
          .substring(2, 15)}.${fileExt}`;
        const filePath = fileName;

        // Upload to Supabase Storage
        const { data, error } = await supabase.storage
          .from(STORAGE_BUCKET)
          .upload(filePath, file, {
            cacheControl: "3600",
            upsert: false,
          });

        if (error) {
          console.error("Error uploading image:", error);
          throw error;
        }

        // Get public URL
        const { data: urlData } = supabase.storage
          .from(STORAGE_BUCKET)
          .getPublicUrl(filePath);

        if (urlData?.publicUrl) {
          uploadedUrls.push(urlData.publicUrl);
        } else {
          console.error("Failed to get public URL for:", filePath);
        }
      } catch (error) {
        console.error("Error uploading image to storage:", error);
        alert(
          t("imageUploadError") ||
            `Failed to upload ${file.name}. Please try again.`
        );
        throw error;
      }
    }

    return uploadedUrls;
  };

  const handleSubmitPost = async (e) => {
    e.preventDefault();
    if (
      !newPost.content.trim() ||
      !newPost.author_name.trim() ||
      !newPost.author_email.trim()
    ) {
      alert(t("forumFillAllFields") || "Please fill all fields");
      return;
    }

    setPosting(true);
    setUploadingImages(true);

    try {
      // Upload images to Supabase Storage first
      let imageUrls = [];
      if (selectedImages.length > 0) {
        try {
          imageUrls = await uploadImagesToStorage(selectedImages);
        } catch (uploadError) {
          console.error("Image upload failed:", uploadError);
          setUploadingImages(false);
          setPosting(false);
          return; // Stop if image upload fails
        }
      }

      setUploadingImages(false);

      // Create post with image URLs
      const params = {
        complaint_id: complaintId,
        author_name: newPost.author_name,
        author_email: newPost.author_email,
        content: newPost.content,
      };

      // Add image URLs if any were uploaded
      if (imageUrls.length > 0) {
        params.image_urls = imageUrls.join(",");
      }

      const response = await axios.post(
        `${API_BASE_URL}/api/forum/post`,
        null,
        { params }
      );
      if (response.data.success) {
        // Clean up object URLs
        imagePreviews.forEach((preview) => {
          if (preview.url && preview.url.startsWith("blob:")) {
            URL.revokeObjectURL(preview.url);
          }
        });

        setNewPost({
          author_name: newPost.author_name,
          author_email: newPost.author_email,
          content: "",
        });
        setSelectedImages([]);
        setImagePreviews([]);
        await fetchForumData();
      } else {
        const errorMsg =
          response.data.error ||
          response.data.message ||
          "Failed to create post";
        alert(errorMsg);
      }
    } catch (err) {
      const errorMsg =
        err.response?.data?.error ||
        err.response?.data?.message ||
        err.message ||
        "Failed to create post. Please check if the forum feature is set up correctly.";
      alert(errorMsg);
      console.error("Post error:", err);
    } finally {
      setPosting(false);
      setUploadingImages(false);
    }
  };

  if (loading) {
    return (
      <div className="forum-loading">
        <div className="loading-spinner"></div>
        <p>{t("forumLoading") || "Loading forum..."}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="forum-error">
        <AlertCircle size={24} />
        <p>{error}</p>
        <button onClick={fetchForumData} className="btn btn-primary">
          {t("retry") || "Retry"}
        </button>
      </div>
    );
  }

  return (
    <div className="forum">
      <div className="forum-header">
        <div>
          <h1>{t("forumTitle") || "Community Forum"}</h1>
          <p>
            {t("forumSubtitle") ||
              "Discuss and vote on this complaint. Similar incidents can upvote to increase priority."}
          </p>
        </div>
        {forumData && (
          <div className="forum-stats">
            <div className="stat-badge">
              <ThumbsUp size={18} />
              <span>
                {forumData.upvote_count || 0} {t("upvotes") || "Upvotes"}
              </span>
            </div>
            <div className="stat-badge">
              <MessageCircle size={18} />
              <span>
                {forumData.post_count || 0} {t("posts") || "Posts"}
              </span>
            </div>
            {forumData.community_priority_boost > 0 && (
              <div className="stat-badge priority">
                <TrendingUp size={18} />
                <span>
                  {t("communityBoost") || "Community Boost"}:{" "}
                  {(forumData.community_priority_boost * 100).toFixed(0)}%
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Voting Section */}
      <div className="forum-voting">
        <h2>{t("voteOnComplaint") || "Vote on this Complaint"}</h2>
        <p className="voting-description">
          {t("votingDescription") ||
            "If you have a similar incident, vote to increase priority. High upvotes can boost urgency!"}
        </p>
        <div className="voting-inputs">
          <input
            type="text"
            placeholder={t("yourName") || "Your Name"}
            value={newPost.author_name}
            onChange={(e) =>
              setNewPost({ ...newPost, author_name: e.target.value })
            }
            className="voting-input"
          />
          <input
            type="email"
            placeholder={t("yourEmail") || "Your Email"}
            value={newPost.author_email}
            onChange={(e) =>
              setNewPost({ ...newPost, author_email: e.target.value })
            }
            className="voting-input"
          />
        </div>
        <div className="voting-buttons">
          <button
            className="btn btn-upvote"
            onClick={() => handleVote("upvote")}
            disabled={voting || !newPost.author_email}
          >
            <ThumbsUp size={18} />
            <span>{t("upvote") || "Upvote"}</span>
            {forumData && (
              <span className="vote-count">{forumData.upvote_count || 0}</span>
            )}
          </button>
          <button
            className="btn btn-downvote"
            onClick={() => handleVote("downvote")}
            disabled={voting || !newPost.author_email}
          >
            <ThumbsDown size={18} />
            <span>{t("downvote") || "Downvote"}</span>
          </button>
        </div>
        {forumData && forumData.upvote_count >= 10 && (
          <div className="priority-notice">
            <AlertCircle size={16} />
            <span>
              {t("priorityBoostActive") ||
                "This complaint has high community support! Urgency may be boosted."}
            </span>
          </div>
        )}
      </div>

      {/* Similar Complaints */}
      {forumData &&
        forumData.similar_complaints &&
        forumData.similar_complaints.length > 0 && (
          <div className="forum-section">
            <h2>
              <Users size={20} />
              {t("similarIncidents") || "Similar Incidents"}
            </h2>
            <div className="similar-complaints">
              {forumData.similar_complaints.map((complaint) => (
                <div key={complaint.id} className="similar-complaint-card">
                  <div className="complaint-header">
                    <span className="complaint-id">
                      #{complaint.id.slice(0, 8)}
                    </span>
                    <span
                      className={`urgency-badge urgency-${complaint.urgency}`}
                    >
                      {complaint.urgency.toUpperCase()}
                    </span>
                  </div>
                  <p className="complaint-description">
                    {complaint.description.substring(0, 150)}...
                  </p>
                  <div className="complaint-footer">
                    <span className="upvote-count">
                      <ThumbsUp size={14} />
                      {complaint.upvote_count || 0}
                    </span>
                    <span className="complaint-date">
                      {formatDistanceToNow(new Date(complaint.created_at), {
                        addSuffix: true,
                      })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      {/* Forum Posts */}
      <div className="forum-section">
        <h2>
          <MessageCircle size={20} />
          {t("discussions") || "Discussions"}
        </h2>

        {/* Create Post Form */}
        <form onSubmit={handleSubmitPost} className="post-form">
          <div className="form-row">
            <input
              type="text"
              placeholder={t("yourName") || "Your Name"}
              value={newPost.author_name}
              onChange={(e) =>
                setNewPost({ ...newPost, author_name: e.target.value })
              }
              required
            />
            <input
              type="email"
              placeholder={t("yourEmail") || "Your Email"}
              value={newPost.author_email}
              onChange={(e) =>
                setNewPost({ ...newPost, author_email: e.target.value })
              }
              required
            />
          </div>
          <textarea
            placeholder={
              t("postPlaceholder") ||
              "Share your experience or thoughts about this complaint..."
            }
            value={newPost.content}
            onChange={(e) =>
              setNewPost({ ...newPost, content: e.target.value })
            }
            rows="4"
            required
          />

          {/* Image Upload Section */}
          <div className="image-upload-section">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageSelect}
              accept="image/*"
              multiple
              style={{ display: "none" }}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="btn btn-image-upload"
            >
              <ImageIcon size={18} />
              {t("uploadImages") || "Upload Images"}
            </button>
            {imagePreviews.length > 0 && (
              <div className="image-previews">
                {imagePreviews.map((preview, index) => (
                  <div key={index} className="image-preview">
                    <img src={preview.url} alt={preview.name} />
                    <button
                      type="button"
                      onClick={() => removeImage(index)}
                      className="remove-image-btn"
                    >
                      <X size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <button type="submit" className="btn btn-primary" disabled={posting}>
            {posting ? t("posting") || "Posting..." : t("post") || "Post"}
          </button>
        </form>

        {/* Posts List */}
        <div className="posts-list">
          {forumData && forumData.posts && forumData.posts.length > 0 ? (
            forumData.posts.map((post) => (
              <div key={post.id} className="forum-post">
                <div className="post-header">
                  <div>
                    <span className="post-author">{post.author_name}</span>
                    <span className="post-date">
                      {formatDistanceToNow(new Date(post.created_at), {
                        addSuffix: true,
                      })}
                    </span>
                  </div>
                </div>
                <div className="post-content">{post.content}</div>

                {/* Display Images */}
                {post.image_urls &&
                  Array.isArray(post.image_urls) &&
                  post.image_urls.length > 0 && (
                    <div className="post-images">
                      {post.image_urls.map((imageUrl, index) => (
                        <div key={index} className="post-image-container">
                          <img
                            src={imageUrl}
                            alt={`Post image ${index + 1}`}
                            onClick={() => window.open(imageUrl, "_blank")}
                            className="post-image"
                          />
                        </div>
                      ))}
                    </div>
                  )}

                <div className="post-footer">
                  <span className="post-upvotes">
                    <ThumbsUp size={14} />
                    {post.upvotes || 0}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className="no-posts">
              <MessageCircle size={48} />
              <p>
                {t("noPostsYet") ||
                  "No discussions yet. Be the first to share your experience!"}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Forum;
