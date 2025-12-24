# Deployment & Stability Notes

- **CORS:** Backend allows all origins (`allow_origins=["*"]`, no cookies). If you tighten it, you must include every live frontend origin, or login/admin calls will fail with CORS.
- **Auto-migrations:** When adding model fields, also update `app/main.py` auto-migration block so columns exist on deploy. Missing columns will crash startup or first request.
- **Profile responses:** Don’t set attributes on SQLAlchemy model properties in responses (e.g., `has_gdrive_creds`). Build response DTOs instead (see `/auth/me`).
- **Google Drive uploads:** Projects/users need `gdrive_folder`, `gdrive_email`, and encrypted `gdrive_creds`. Share the folder with the service account email to avoid 403s. Transcripts surface `gdrive_error_message`; check it before assuming success.
- **User deletion:** Use DELETE `/admin/users/{id}` (soft delete). Data is retained for 10 days; don’t hard-delete rows.
- **Project management UI:** Use the “Manage” button in the admin project list to edit folder/email/JSON. Avoid reintroducing a separate “connect project” card.
- **Post-deploy checks:** After deploy, verify `/docs` routes exist and call `/auth/me` from the live frontend URL to confirm CORS. Test `/auth/token`, `/projects/admin`, and `/admin/users` from the frontend domain.
