import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import type { Dispatch, SetStateAction } from "react";
import keycloak from "../keycloak";
import "./AdminPanel.css";
import axios from "axios";

interface AdminPanelProps {
  setIsLoggedIn: Dispatch<SetStateAction<boolean>>;
}

interface Post {
  id: number;
  provider: string;
  source_url: string;
  reason: string | null;
  author: string | null;
  description: string | null;
  image_url: string;
  keywords: string[] | null;
  status: "pending" | "approved" | "rejected" | "blacklisted";
}

const AdminPanel = ({ setIsLoggedIn }: AdminPanelProps) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("moderation");
  const [posts, setPosts] = useState<Post[]>([]);
  const [filter, setFilter] = useState<
    "all" | "pending" | "approved" | "rejected" | "suspended" | "blocked"
  >("all");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!keycloak.authenticated) {
      navigate("/login");
      return;
    }

    const roles = keycloak.tokenParsed?.realm_access?.roles || [];
    if (!roles.includes("admin")) {
      navigate("/");
    }
  }, [navigate]);

  useEffect(() => {
    fetchPosts();
  }, [filter]);

  const fetchPosts = async () => {
    setLoading(true);
    let url: string;

    switch (filter) {
      case "all":
        url = "/api/posts?provider=PHOTO-SEARCH";
        break;
      case "suspended":
        url = "/api/blacklist/suspended";
        break;
      case "blocked":
        url = "/api/blacklist/blocked";
        break;
      default:
        url = `/api/admin/posts?status=${filter}`;
        break;
    }

    axios
        .get(url, {headers: {
          Authorization: `Bearer ${keycloak.token}`,
          },
        })
        .then((response) => {
          setPosts(response.data || []);
        })
        .catch((error) => console.error(error))
        .finally(() => setLoading(false));
  };

  const handleApprove = async (postId: number) => {
    try {
      const response = await fetch(
        `http://localhost:5001/api/admin/posts/${postId}/approve`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${keycloak.token}`,
          },
        }
      );

      if (response.ok) {
        fetchPosts();
      }
    } catch (error) {
      console.error("Error approving post:", error);
    }
  };

  const handleReject = async (postId: number) => {
    try {
      const response = await fetch(
        `http://localhost:5001/api/admin/posts/${postId}/reject`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${keycloak.token}`,
          },
        }
      );

      if (response.ok) {
        fetchPosts();
      }
    } catch (error) {
      console.error("Error rejecting post:", error);
    }
  };

  const handleDelete = async (postId: number) => {
    if (!confirm("Are you sure you want to delete this post?")) return;

    axios
        .delete(`/api/admin/posts/${postId}`, {headers: {
          Authorization: `Bearer ${keycloak.token}`,
          }})
        .then(() => fetchPosts())
        .catch((error) => console.error("Error deleting post:", error))
  };

  const handleLogout = () => {
    keycloak.logout({
      redirectUri: window.location.origin + "/",
    });
    setIsLoggedIn(false);
  };

  const handleBlock = async (postId: number) => {
    axios
        .patch(`/api/blacklist/block/${postId}`, null,  {headers: {
          Authorization: `Bearer ${keycloak.token}`,
          }})
        .then(() => fetchPosts())
        .catch((error) => console.error(error))
  }

  const handleUnlock = async (postId: number) => {
    axios
        .delete(`/api/blacklist/${postId}`, {headers: {
            Authorization: `Bearer ${keycloak.token}`,
          }
        })
        .then(()=> fetchPosts())
        .catch((error) => console.error(error))
  }

  const user = {
    username: keycloak.tokenParsed?.preferred_username || "Admin",
    email: keycloak.tokenParsed?.email || "No email",
  };

  return (
    <div className="admin-panel-container">
      <h1>Admin Panel</h1>
      <div className="tabs">
        <button
          className={`tab-button ${activeTab === "moderation" ? "active" : ""}`}
          onClick={() => setActiveTab("moderation")}
        >
          Posts Moderation
        </button>
        <button
          className={`tab-button ${activeTab === "info" ? "active" : ""}`}
          onClick={() => setActiveTab("info")}
        >
          Account Information
        </button>
        <button
          className={`tab-button ${activeTab === "logout" ? "active" : ""}`}
          onClick={() => setActiveTab("logout")}
        >
          Log Out
        </button>
      </div>

      <div className="tab-content">
        {activeTab === "moderation" && (
          <div className="moderation-section">
            <div className="filter-buttons">
              <button
                className={filter === "all" ? "active" : ""}
                onClick={() => setFilter("all")}
              >
                All
              </button>
              <button
                className={filter === "pending" ? "active" : ""}
                onClick={() => setFilter("pending")}
              >
                Pending
              </button>
              <button
                className={filter === "approved" ? "active" : ""}
                onClick={() => setFilter("approved")}
              >
                Approved
              </button>
              <button
                className={filter === "rejected" ? "active" : ""}
                onClick={() => setFilter("rejected")}
              >
                Rejected
              </button>
              <button
                className={filter === "suspended" ? "active" : ""}
                onClick={() => setFilter("suspended")}
              >
                Suspended
              </button>
              <button
                className={filter === "blocked" ? "active" : ""}
                onClick={() => setFilter("blocked")}
              >
                  Blocked
              </button>
            </div>

            {loading ? (
              <p>Loading...</p>
            ) : posts.length === 0 ? (
              <p>No posts found.</p>
            ) : (
              <div className="posts-grid">
                {posts.map((post) => (
                  <div
                    key={post.id}
                    className={`post-card status-${post.status === "blacklisted" ? "pending" : post.status}`}
                  >
                    <img src={post.image_url} alt={post.description || `Post ${post.id}`} />
                    <div className="post-info">
                      {post.description && (
                          <p>
                            <strong>Description:</strong> {post.description}
                          </p>)}
                      {post.keywords && (<p>
                        <strong>Keywords:</strong> {post.keywords.join(", ")}
                      </p>)}
                      {post.status !== "blacklisted" && (<p>
                        <strong>Status:</strong>{" "}
                        <span className={`status-badge ${post.status}`}>
                          {post.status}
                        </span>
                      </p>)}
                    </div>
                    <div className="post-actions">
                      {post.status !== "blacklisted" ? (
                          <>
                            {post.status !== "approved" && (
                                <button
                                    className="approve-btn"
                                    onClick={() => handleApprove(post.id)}
                                >
                                  ✓ Approve
                                </button>
                            )}
                            {post.status !== "rejected" && (
                                <button
                                    className="reject-btn"
                                    onClick={() => handleReject(post.id)}
                                >
                                  ✗ Reject
                                </button>
                            )}
                          </>
                      ) : (
                          <>
                            <button
                                className="approve-btn"
                                onClick={() => handleUnlock(post.id)}
                            >
                              Unlock
                            </button>
                            {filter === "suspended" && (
                                <button
                                    className="delete-btn"
                                    onClick={() => handleBlock(post.id)}
                                >
                                  Block
                                </button>
                            )}
                          </>
                      )}
                      <button
                        className="delete-btn"
                        onClick={() => handleDelete(post.id)}
                      >
                        🗑 Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "info" && (
          <div className="user-info">
            <p>
              <strong>Username:</strong> {user.username}
            </p>
            <p>
              <strong>Email:</strong> {user.email}
            </p>
            <p>
              <strong>Role:</strong> Administrator
            </p>
          </div>
        )}

        {activeTab === "logout" && (
          <div>
            <p>Are you sure you want to log out?</p>
            <button onClick={handleLogout} className="logout-button">
              Yes, Log Out
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminPanel;
