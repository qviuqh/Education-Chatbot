# Frontend/Backend Integration Issues

## Missing API version prefix
- The backend mounts all routers under the `API_V1_PREFIX` (`/api/v1`), so every endpoint is available with this prefix (e.g., `/api/v1/auth/login/json`, `/api/v1/subjects`).
- The frontend currently calls endpoints without the prefix (base URL `http://localhost:8000` and paths like `/auth/me`, `/subjects`, `/chat/stream`). These requests will return 404 because the backend paths are `/api/v1/...`.

## Conversation creation requires at least one document
- The backend schema enforces `document_ids` to have at least one entry when creating a conversation.
- The frontend allows creating a conversation even when no documents are selected (passes an empty `selectedDocs` array). This results in a 422 validation error from the backend.

## File upload and other requests affected by missing prefix
- Uploads to `/subjects/{subject_id}/documents` and chat streaming to `/chat/stream` are sent without the `/api/v1` prefix, leading to failed uploads or streaming errors because the backend routes include the prefix.
