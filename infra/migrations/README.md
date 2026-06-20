# Database migrations

Initialize Alembic:

```bash
alembic init infra/migrations/alembic
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

Models are defined in `services/api/core/models.py`. For Supabase, apply the same schema via SQL editor with RLS policies enabled.
