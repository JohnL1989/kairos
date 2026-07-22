-- migrations/reflector_role.sql
-- A-03 修复配套：为 reflector 提供最小权限数据库角色。
--
-- 背景：reflector.py 直连数据库、绕过 API 认证/限流/审计中间件。若以全权限
-- （如 postgres 或应用主账号）运行，一旦 reflector 逻辑/依赖被攻破，攻击者即
-- 拥有 DELETE / DROP / 任意写 的能力。本脚本创建仅授予 SELECT/UPDATE（+ deep
-- 模式实体提取所需的 entities INSERT）的角色，使 reflector 的「热度衰减 +
-- 冗余软删（is_deleted=TRUE 的 UPDATE）+ deep 实体提取」可运行，但无法物理
-- DELETE、执行 DDL 或越权写其它表。
--
-- 使用：
--   1) 用管理员账号执行本脚本（替换 <REFLECTOR_PASSWORD>）。
--   2) 将 reflector 的连接串写入 MNEMOSYNE_REFLECTOR_DSN，例如：
--      postgresql://amber_reflector:<REFLECTOR_PASSWORD>@127.0.0.1:5432/amber
--   3) 不要再给 reflector 使用应用主账号 / postgres。

-- 1. 角色（登录用）
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amber_reflector') THEN
        CREATE ROLE amber_reflector LOGIN PASSWORD '<REFLECTOR_PASSWORD>';
    END IF;
END$$;

-- 2. 连接与 schema 使用权（不含 CREATE）
GRANT CONNECT ON DATABASE amber TO amber_reflector;
GRANT USAGE ON SCHEMA public TO amber_reflector;

-- 3. 表级最小权限：仅 SELECT / UPDATE。
--    冗余合并采用「软删」(UPDATE memories SET is_deleted=TRUE)，无需 DELETE。
--    实体转移是 UPDATE memory_entities，无需 INSERT/DELETE。
--    deep 模式实体提取会 INSERT INTO entities（仅新增，不删除），故授予 SELECT/INSERT。
GRANT SELECT, UPDATE ON memories TO amber_reflector;
GRANT SELECT, UPDATE ON memory_entities TO amber_reflector;
GRANT SELECT, INSERT ON entities TO amber_reflector;
-- reflect() 服务层若需读取以下表，仅给只读权限（按实际用到的表增减）
GRANT SELECT ON memory_traces TO amber_reflector;

-- 4. 明确回收危险权限（防止 PUBLIC 默认授予残留）。
--    entities 仅保留 SELECT/INSERT（deep 模式新增实体用），回收 DELETE 等。
REVOKE INSERT, DELETE, TRUNCATE, REFERENCES, TRIGGER ON memories FROM amber_reflector;
REVOKE INSERT, DELETE, TRUNCATE, REFERENCES, TRIGGER ON memory_entities FROM amber_reflector;
REVOKE DELETE, TRUNCATE, REFERENCES, TRIGGER ON entities FROM amber_reflector;

-- 5. 序列不授予（无 INSERT 需求）；未来新表默认不授权，需显式 GRANT。
-- 说明：不设置 ALTER DEFAULT PRIVILEGES，确保新表默认对 reflector 不可见，
--       遵循「最小惊讶 + 显式授权」原则。
