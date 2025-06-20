from flask import jsonify, request
from app.api import bp
from app.models import Post, User
from app import db
from datetime import datetime
import os
from sqlalchemy import text
from app.cache import cache


try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@bp.route("/posts", methods=["GET"])
@cache.memoize(timeout=60)
def get_posts():
    """Get all posts with pagination (cached)"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify(
        {
            "posts": [post.to_dict() for post in posts.items],
            "total": posts.total,
            "pages": posts.pages,
            "current_page": posts.page,
        }
    )


@bp.route("/posts/<int:id>", methods=["GET"])
@cache.memoize(timeout=300)
def get_post(id):
    """Get a specific post by ID (cached)"""
    post = Post.query.get_or_404(id)
    response = post.to_dict()
    response["cached"] = True
    return jsonify(response)


@bp.route("/posts", methods=["POST"])
def create_post():
    """Create a new post"""
    data = request.get_json() or {}

    if "body" not in data:
        return jsonify({"error": "Post body is required"}), 400

    if "user_id" not in data:
        return jsonify({"error": "User ID is required"}), 400

    user = User.query.get(data["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    post = Post(body=data["body"], user_id=data["user_id"])
    db.session.add(post)
    db.session.commit()

    cache.delete_memoized(get_posts)

    return jsonify(post.to_dict()), 201


@bp.route("/posts/<int:id>", methods=["PUT"])
def update_post(id):
    """Update an existing post"""
    post = Post.query.get_or_404(id)
    data = request.get_json() or {}

    if "body" in data:
        post.body = data["body"]

    db.session.commit()

    cache.delete_memoized(get_posts)
    cache.delete_memoized(get_post, id)

    return jsonify(post.to_dict())


@bp.route("/posts/<int:id>", methods=["DELETE"])
def delete_post(id):
    """Delete a post"""
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()

    cache.delete_memoized(get_posts)
    cache.delete_memoized(get_post, id)

    return jsonify({"message": "Post deleted successfully"}), 200


@bp.route("/users", methods=["GET"])
def get_users():
    """Get all users"""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])


@bp.route("/users/<int:id>", methods=["GET"])
def get_user(id):
    """Get a specific user by ID"""
    user = User.query.get_or_404(id)
    return jsonify(user.to_dict())


@bp.errorhandler(404)
def handle_404(error):
    return jsonify({"error": "Resource not found"}), 404


@bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("VERSION", "unknown"),
        "checks": {},
    }

    try:
        db.session.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    if HAS_PSUTIL:
        try:
            memory = psutil.virtual_memory()
            health_status["checks"]["memory"] = {
                "usage_percent": memory.percent,
                "available_mb": round(memory.available / 1024 / 1024, 2),
            }

            disk = psutil.disk_usage("/")
            health_status["checks"]["disk"] = {
                "usage_percent": disk.percent,
                "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
            }
        except Exception as e:
            health_status["checks"]["system"] = f"psutil error: {str(e)}"
    else:
        health_status["checks"][
            "system"
        ] = "psutil not available (basic health check only)"

    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code


@bp.route("/metrics", methods=["GET"])
def metrics():
    """Prometheus metrics endpoint"""
    metrics_data = []

    total_posts = Post.query.count()
    total_users = User.query.count()

    metrics_data.extend(
        [
            f"flask_app_posts_total {total_posts}",
            f"flask_app_users_total {total_users}",
        ]
    )

    if HAS_PSUTIL:
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()

            metrics_data.extend(
                [
                    f"flask_app_memory_usage_percent {memory.percent}",
                    f"flask_app_cpu_usage_percent {cpu_percent}",
                ]
            )
        except Exception:
            metrics_data.append("flask_app_system_metrics_error 1")
    else:
        metrics_data.append("flask_app_psutil_available 0")

    return "\n".join(metrics_data), 200, {"Content-Type": "text/plain"}


@bp.route("/ready", methods=["GET"])
def readiness_check():
    """Readiness check for Kubernetes"""
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ready"}), 200
    except Exception as e:
        return jsonify({"status": "not ready", "error": str(e)}), 503


@bp.route("/cache/clear", methods=["POST"])
def clear_cache():
    """Clear all cache entries"""
    try:
        cache.clear()
        return jsonify({"message": "Cache cleared successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to clear cache: {str(e)}"}), 500


@bp.route("/cache/info", methods=["GET"])
def cache_info():
    """Get cache information"""
    try:
        redis_client = cache.cache._write_client
        info = redis_client.info()

        return jsonify(
            {
                "cache_type": "Redis",
                "connected_clients": info.get("connected_clients", "unknown"),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "keyspace_hits": info.get("keyspace_hits", "unknown"),
                "keyspace_misses": info.get("keyspace_misses", "unknown"),
                "hit_rate": round(
                    info.get("keyspace_hits", 0)
                    / max(
                        1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)
                    )
                    * 100,
                    2,
                ),
            }
        )
    except Exception as e:
        return jsonify({"error": f"Could not get cache info: {str(e)}"}), 500


@bp.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request"}), 400
