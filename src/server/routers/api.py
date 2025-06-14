"""API endpoints for programmatic access to Gitingest functionality."""

from typing import Dict, Optional, Set

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from gitingest.cloning import clone_repo
from gitingest.ingestion import ingest_query
from gitingest.query_parsing import IngestionQuery, parse_query
from server.server_utils import limiter

router = APIRouter(prefix="/api/v1", tags=["api"])


class IngestRequest(BaseModel):
    """Request model for repository ingestion."""
    
    source: str = Field(..., description="Git repository URL or local path")
    max_file_size: Optional[int] = Field(
        default=10 * 1024 * 1024, 
        description="Maximum file size to process in bytes",
        ge=1024,  # At least 1KB
        le=100 * 1024 * 1024  # At most 100MB
    )
    include_patterns: Optional[Set[str]] = Field(
        default=None,
        description="Patterns to include (Unix shell-style wildcards)"
    )
    exclude_patterns: Optional[Set[str]] = Field(
        default=None,
        description="Patterns to exclude (Unix shell-style wildcards)"
    )
    branch: Optional[str] = Field(
        default=None,
        description="Specific branch to clone and ingest"
    )


class IngestResponse(BaseModel):
    """Response model for repository ingestion."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    data: Optional[Dict[str, str]] = Field(
        default=None,
        description="Ingestion results containing summary, tree, and content"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if operation failed"
    )
    metadata: Optional[Dict[str, str]] = Field(
        default=None,
        description="Additional metadata about the ingestion"
    )


@router.post("/ingest", response_model=IngestResponse)
@limiter.limit("5/minute")
async def ingest_repository(request: Request, body: IngestRequest) -> IngestResponse:
    """
    Ingest a Git repository and return structured results.
    
    This endpoint processes a Git repository URL or local path and returns
    the repository contents in a structured format suitable for LLMs.
    
    Args:
        request: FastAPI Request object (for rate limiting)
        body: IngestRequest containing source and processing parameters
        
    Returns:
        IngestResponse with success status and data or error information
        
    Raises:
        HTTPException: If the request is invalid or processing fails
    """
    try:
        # Parse the query using existing logic
        query: IngestionQuery = await parse_query(
            source=body.source,
            max_file_size=body.max_file_size,
            from_web=True,
            include_patterns=body.include_patterns,
            ignore_patterns=body.exclude_patterns,
        )
        
        # Override branch if specified in request
        if body.branch:
            query.branch = body.branch
        
        # Clone repository if it's a remote URL
        if query.url:
            clone_config = query.extract_clone_config()
            await clone_repo(clone_config)
        
        # Perform ingestion
        summary, tree, content = ingest_query(query)
        
        # Prepare metadata
        metadata = {
            "source_type": "remote" if query.url else "local",
            "repository": f"{query.user_name}/{query.repo_name}" if query.user_name else query.slug,
            "branch": query.branch or "default",
            "subpath": query.subpath,
        }
        
        return IngestResponse(
            success=True,
            data={
                "summary": summary,
                "tree": tree,
                "content": content
            },
            metadata=metadata
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        return IngestResponse(
            success=False,
            error=str(e)
        )


@router.get("/ingest", response_model=IngestResponse)
@limiter.limit("5/minute")
async def ingest_repository_get(
    request: Request,  # Required for slowapi rate limiter
    source: str,
    max_file_size: Optional[int] = 10 * 1024 * 1024,
    include_patterns: Optional[str] = None,
    exclude_patterns: Optional[str] = None,
    branch: Optional[str] = None
) -> IngestResponse:
    """
    Ingest a repository using GET method with query parameters.
    
    This endpoint provides the same functionality as the POST endpoint
    but accepts parameters as URL query parameters for easier testing.
    
    Args:
        source: Git repository URL or local path
        max_file_size: Maximum file size to process in bytes
        include_patterns: Comma-separated patterns to include
        exclude_patterns: Comma-separated patterns to exclude
        branch: Specific branch to clone and ingest
        
    Returns:
        IngestResponse with success status and data or error information
    """
    # Parse comma-separated patterns
    include_set = None
    if include_patterns:
        include_set = {p.strip() for p in include_patterns.split(',') if p.strip()}
    
    exclude_set = None
    if exclude_patterns:
        exclude_set = {p.strip() for p in exclude_patterns.split(',') if p.strip()}
    
    # Create request object and delegate to POST handler
    body = IngestRequest(
        source=source,
        max_file_size=max_file_size,
        include_patterns=include_set,
        exclude_patterns=exclude_set,
        branch=branch
    )
    
    return await ingest_repository(request, body)


@router.get("/ingest/summary", response_model=Dict[str, str])
@limiter.limit("10/minute")
async def get_repository_summary(
    request: Request,  # Required for slowapi rate limiter
    source: str,
    branch: Optional[str] = None
) -> Dict[str, str]:
    """
    Get only the summary information for a repository.
    
    This is a lightweight endpoint that returns only the summary
    without the full directory tree and file contents.
    
    Args:
        request: FastAPI Request object (for rate limiting)
        source: Git repository URL or local path
        branch: Specific branch to analyze
        
    Returns:
        Dictionary containing source and summary information
        
    Raises:
        HTTPException: If the repository cannot be processed
    """
    try:
        body = IngestRequest(source=source, branch=branch)
        response = await ingest_repository(request, body)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)
        
        return {
            "source": source,
            "summary": response.data["summary"],
            "repository": response.metadata.get("repository", ""),
            "branch": response.metadata.get("branch", "")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def api_health_check() -> Dict[str, str]:
    """
    Health check endpoint for the API.
    
    Returns:
        Simple status message indicating the API is operational
    """
    return {"status": "healthy", "service": "gitingest-api"} 