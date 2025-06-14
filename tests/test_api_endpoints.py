"""Tests for the API endpoints."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


class TestAPIEndpoints:
    """Test class for API endpoints."""

    def test_api_health_check(self):
        """Test the API health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "gitingest-api"

    @patch("server.routers.api.clone_repo")
    @patch("server.routers.api.ingest_query")
    @patch("server.routers.api.parse_query")
    def test_ingest_repository_post_success(self, mock_parse_query, mock_ingest_query, mock_clone_repo):
        """Test successful repository ingestion via POST."""
        # Mock parse_query
        mock_query = AsyncMock()
        mock_query.url = "https://github.com/test/repo"
        mock_query.user_name = "test"
        mock_query.repo_name = "repo"
        mock_query.branch = "main"
        mock_query.subpath = "/"
        mock_query.extract_clone_config.return_value = AsyncMock()
        mock_parse_query.return_value = mock_query

        # Mock ingest_query
        mock_ingest_query.return_value = (
            "Repository: test/repo\nFiles analyzed: 5",
            "test-repo/\n├── src/\n│   └── main.py\n└── README.md",
            "FILE: src/main.py\n...\n\nFILE: README.md\n..."
        )

        # Mock clone_repo
        mock_clone_repo.return_value = None

        request_data = {
            "source": "https://github.com/test/repo",
            "max_file_size": 1048576,
            "include_patterns": ["*.py"],
            "branch": "main"
        }

        response = client.post("/api/v1/ingest", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "summary" in data["data"]
        assert "tree" in data["data"]
        assert "content" in data["data"]
        assert data["metadata"]["source_type"] == "remote"
        assert data["metadata"]["repository"] == "test/repo"

    def test_ingest_repository_post_invalid_data(self):
        """Test repository ingestion with invalid data."""
        request_data = {
            "source": "",  # Empty source should fail validation
            "max_file_size": 500  # Too small, should fail validation
        }

        response = client.post("/api/v1/ingest", json=request_data)
        assert response.status_code == 422  # Validation error

    @patch("server.routers.api.clone_repo")
    @patch("server.routers.api.ingest_query")
    @patch("server.routers.api.parse_query")
    def test_ingest_repository_get_success(self, mock_parse_query, mock_ingest_query, mock_clone_repo):
        """Test successful repository ingestion via GET."""
        # Mock parse_query
        mock_query = AsyncMock()
        mock_query.url = "https://github.com/test/repo"
        mock_query.user_name = "test"
        mock_query.repo_name = "repo"
        mock_query.branch = "main"
        mock_query.subpath = "/"
        mock_query.extract_clone_config.return_value = AsyncMock()
        mock_parse_query.return_value = mock_query

        # Mock ingest_query
        mock_ingest_query.return_value = (
            "Repository: test/repo\nFiles analyzed: 3",
            "test-repo/\n├── main.py\n└── README.md",
            "FILE: main.py\n...\n\nFILE: README.md\n..."
        )

        # Mock clone_repo
        mock_clone_repo.return_value = None

        response = client.get(
            "/api/v1/ingest",
            params={
                "source": "https://github.com/test/repo",
                "max_file_size": 2097152,
                "include_patterns": "*.py,*.md",
                "branch": "develop"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "summary" in data["data"]
        assert "tree" in data["data"]
        assert "content" in data["data"]

    @patch("server.routers.api.clone_repo")
    @patch("server.routers.api.ingest_query")
    @patch("server.routers.api.parse_query")
    def test_get_repository_summary_success(self, mock_parse_query, mock_ingest_query, mock_clone_repo):
        """Test successful repository summary retrieval."""
        # Mock parse_query
        mock_query = AsyncMock()
        mock_query.url = "https://github.com/test/repo"
        mock_query.user_name = "test"
        mock_query.repo_name = "repo"
        mock_query.branch = "main"
        mock_query.subpath = "/"
        mock_query.extract_clone_config.return_value = AsyncMock()
        mock_parse_query.return_value = mock_query

        # Mock ingest_query
        mock_ingest_query.return_value = (
            "Repository: test/repo\nFiles analyzed: 8\nEstimated tokens: 1.2k",
            "tree...",
            "content..."
        )

        # Mock clone_repo
        mock_clone_repo.return_value = None

        response = client.get(
            "/api/v1/ingest/summary",
            params={
                "source": "https://github.com/test/repo",
                "branch": "main"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "source" in data
        assert "summary" in data
        assert "repository" in data
        assert "branch" in data
        assert data["source"] == "https://github.com/test/repo"
        assert "test/repo" in data["summary"]

    def test_get_repository_summary_missing_source(self):
        """Test repository summary with missing source parameter."""
        response = client.get("/api/v1/ingest/summary")
        assert response.status_code == 422  # Missing required parameter

    @patch("server.routers.api.parse_query")
    def test_ingest_repository_error_handling(self, mock_parse_query):
        """Test error handling in repository ingestion."""
        # Mock parse_query to raise an exception
        mock_parse_query.side_effect = ValueError("Invalid repository URL")

        request_data = {
            "source": "invalid-url",
            "max_file_size": 1048576
        }

        response = client.post("/api/v1/ingest", json=request_data)
        assert response.status_code == 400
        data = response.json()
        assert "Invalid repository URL" in data["detail"]

    def test_pattern_parsing_in_get_request(self):
        """Test that comma-separated patterns are correctly parsed in GET requests."""
        with patch("server.routers.api.ingest_repository") as mock_ingest:
            mock_ingest.return_value = {
                "success": True,
                "data": {"summary": "test", "tree": "test", "content": "test"},
                "metadata": {}
            }

            response = client.get(
                "/api/v1/ingest",
                params={
                    "source": "https://github.com/test/repo",
                    "include_patterns": "*.py, *.md, *.txt",
                    "exclude_patterns": "*.log,  *.tmp "
                }
            )

            # Verify that the patterns were correctly parsed
            call_args = mock_ingest.call_args[0][0]
            assert call_args.include_patterns == {"*.py", "*.md", "*.txt"}
            assert call_args.exclude_patterns == {"*.log", "*.tmp"}

    def test_request_validation_constraints(self):
        """Test request validation constraints."""
        # Test file size too small
        response = client.post("/api/v1/ingest", json={
            "source": "https://github.com/test/repo",
            "max_file_size": 500  # Less than 1KB minimum
        })
        assert response.status_code == 422

        # Test file size too large
        response = client.post("/api/v1/ingest", json={
            "source": "https://github.com/test/repo",
            "max_file_size": 200 * 1024 * 1024  # More than 100MB maximum
        })
        assert response.status_code == 422

    @patch("server.routers.api.clone_repo")
    @patch("server.routers.api.ingest_query")
    @patch("server.routers.api.parse_query")
    def test_local_path_ingestion(self, mock_parse_query, mock_ingest_query, mock_clone_repo):
        """Test ingestion of local path (no cloning needed)."""
        # Mock parse_query for local path
        mock_query = AsyncMock()
        mock_query.url = None  # No URL for local path
        mock_query.user_name = None
        mock_query.repo_name = None
        mock_query.slug = "local-project"
        mock_query.branch = None
        mock_query.subpath = "/"
        mock_parse_query.return_value = mock_query

        # Mock ingest_query
        mock_ingest_query.return_value = (
            "Directory: local-project\nFiles analyzed: 2",
            "local-project/\n├── main.py\n└── config.json",
            "FILE: main.py\n...\n\nFILE: config.json\n..."
        )

        request_data = {
            "source": "/path/to/local/project",
            "max_file_size": 1048576
        }

        response = client.post("/api/v1/ingest", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["source_type"] == "local"
        assert data["metadata"]["repository"] == "local-project"

        # Ensure clone_repo was not called for local path
        mock_clone_repo.assert_not_called()


# Integration tests (require actual network access)
@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for API endpoints (require network access)."""

    def test_real_repository_ingestion(self):
        """Test ingestion of a real small repository."""
        request_data = {
            "source": "https://github.com/octocat/Hello-World",
            "max_file_size": 1048576,
            "include_patterns": ["*.md"]
        }

        response = client.post("/api/v1/ingest", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "Hello-World" in data["data"]["summary"]
        assert "README" in data["data"]["tree"]

    def test_real_repository_summary(self):
        """Test summary endpoint with a real repository."""
        response = client.get(
            "/api/v1/ingest/summary",
            params={"source": "https://github.com/octocat/Hello-World"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "Hello-World" in data["summary"]
        assert data["repository"] == "octocat/Hello-World" 