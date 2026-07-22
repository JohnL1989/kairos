"""
Mnemosyne v5.0 — 项目管理 API
白皮书 L5 运行时调度层: 项目级沙箱
"""
import asyncpg
from .response import ok, error as api_error
from fastapi import APIRouter, Depends
from .shared import get_current_user, get_pool
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])



class ProjectCreate(BaseModel):
    name: str
    description: str = ""


class ProjectArchive(BaseModel):
    project_id: int


@router.post("/create")
async def create_project(req: ProjectCreate, user_id: str = Depends(get_current_user),
                         pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """创建项目"""
    async with pool.acquire() as conn:
        pid = f"proj_{uuid.uuid4().hex[:12]}"
        row = await conn.fetchrow(
            """INSERT INTO projects (project_id, tenant_id, name, description)
               VALUES ($1, $2, $3, $4) RETURNING id, project_id, created_at""",
            pid, user_id, req.name, req.description
        )
        return ok({
            "id": row["id"],
            "project_id": row["project_id"],
            "name": req.name,
            "created": str(row["created_at"])[:19],
        })


@router.get("/{project_id}")
async def get_project(project_id: int, user_id: str = Depends(get_current_user),
                      pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """查询项目"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM projects WHERE id=$1 AND tenant_id=$2", project_id, user_id
        )
        if not row:
            return api_error(message="项目不存在", code=404, status_code=404)
        
        # 统计项目下的记忆数
        mem_count = await conn.fetchval(
            "SELECT count(*) FROM memories WHERE project_id=$1", project_id
        )
        
        return ok({
            "id": row["id"],
            "project_id": row["project_id"],
            "name": row["name"],
            "description": row["description"],
            "status": row["status"],
            "memory_count": mem_count,
            "created": str(row["created_at"])[:19],
            "updated": str(row["updated_at"])[:19],
        })


@router.post("/{project_id}/archive")
async def archive_project(project_id: int, user_id: str = Depends(get_current_user),
                          pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """归档项目"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE projects SET status='archived', updated_at=NOW() WHERE id=$1 AND tenant_id=$2 RETURNING id",
            project_id, user_id
        )
        if not row:
            return api_error(message="项目不存在", code=404, status_code=404)
        return ok({"id": project_id, "status": "archived", "message": "项目已归档"})


@router.post("/{project_id}/destroy")
async def destroy_project(project_id: int, user_id: str = Depends(get_current_user),
                          pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """销毁项目沙箱 (不可逆)"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE projects SET status='destroyed', updated_at=NOW() WHERE id=$1 AND tenant_id=$2 RETURNING id",
            project_id, user_id
        )
        if not row:
            return api_error(message="项目不存在", code=404, status_code=404)
        # 清除关联记忆的 project_id
        await conn.execute(
            "UPDATE memories SET project_id=NULL WHERE project_id=$1", project_id
        )
        return ok({"id": project_id, "status": "destroyed", "message": "项目沙箱已销毁 (记忆已保留)"})


class ProjectRegister(BaseModel):
    name: str
    workspace_path: str = ""
    description: str = ""


@router.post("/register")
async def register_project(req: ProjectRegister, user_id: str = Depends(get_current_user),
                           pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT id FROM projects WHERE name=$1 AND tenant_id=$2 AND status='active'", req.name, user_id)
        if existing:
            await conn.execute("UPDATE projects SET description=$1, updated_at=NOW() WHERE id=$2", req.description, existing["id"])
            return ok({"action": "updated", "id": existing["id"], "name": req.name})
        pid = f"proj_{uuid.uuid4().hex[:12]}"
        row = await conn.fetchrow("INSERT INTO projects (project_id, tenant_id, name, description) VALUES ($1,$2,$3,$4) RETURNING id", pid, user_id, req.name, req.description)
        return ok({"action": "created", "id": row["id"], "name": req.name, "project_id": pid})

@router.get("/by-name/{name}")
async def get_project_by_name(name: str, user_id: str = Depends(get_current_user),
                              pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id FROM projects WHERE name=$1 AND tenant_id=$2 AND status=$3", name, user_id, "active")
        if not row:
            return api_error(message="项目不存在", code=404, status_code=404)
        memories = await conn.fetch("SELECT id, content, category, heat_score, created_at FROM memories WHERE project_id=$1 AND is_deleted=FALSE ORDER BY created_at DESC LIMIT 50", row["id"])
        return ok({"project": name, "memories": [
            {"id": m["id"], "content": m["content"][:200], "category": m["category"],
             "heat": m["heat_score"], "created": str(m["created_at"])[:19]} for m in memories]})

@router.get("/")
async def list_projects(user_id: str = Depends(get_current_user),
                        pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """列出所有项目"""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT p.*, 
               (SELECT count(*) FROM memories m WHERE m.project_id=p.id) as mem_count
               FROM projects p WHERE p.tenant_id=$1 ORDER BY p.created_at DESC""",
            user_id
        )
        return ok({
            "projects": [
                {
                    "id": r["id"],
                    "project_id": r["project_id"],
                    "name": r["name"],
                    "description": r["description"],
                    "status": r["status"],
                    "memory_count": r["mem_count"],
                    "created": str(r["created_at"])[:19],
                }
                for r in rows
            ],
            "count": len(rows)
        })
