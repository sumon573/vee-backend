# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.7.0] — 2026-07-21

### Added — Phase 9: Direct Messaging Foundation

#### Models
- `app/models/conversation.py` — `Conversation` ORM model (UUIDMixin + TimestampMixin); `ConversationParticipant` junction table with composite PK (conversation_id, user_id), joined_at timestamp, CASCADE DELETE on both FK columns; `ix_conversation_participants_user_id` index
- `app/models/message.py` — `Message` ORM model (UUIDMixin + TimestampMixin); fields: conversation_id (FK CASCADE), sender_id (FK CASCADE), content (TEXT nullable), message_type (MessageType enum), is_deleted (bool, default false); indexes: ix_messages_conversation_id, ix_messages_sender_id, ix_messages_created_at
- `app/models/enums.py` — `MessageType` enum added (TEXT; future: AUDIO, IMAGE)

#### Schemas
- `app/schemas/message.py` — `ParticipantRead`, `ConversationCreate`, `ConversationRead` (with `from_orm_for_viewer()` classmethod), `ConversationListResponse`, `MessageCreate`, `MessageRead`, `MessageListResponse`

#### Repositories
- `app/repositories/conversation_repo.py` — `ConversationRepository`: `create_conversation()`, `get_conversation()`, `get_conversation_between()`, `list_conversations()`, `count_conversations()`
- `app/repositories/message_repo.py` — `MessageRepository`: `get_message()`, `send_message()`, `list_messages()`, `count_messages()`, `mark_deleted()`

#### Service
- `app/services/message_service.py` — `MessageService`: `get_or_create_conversation()`, `list_conversations()`, `send_message()`, `list_messages()`; business rules: no self-message, no blocked recipient (PrivacyGuard.can_message()), no inactive/deleted recipient, duplicate conversation prevention

#### API Endpoints
- `POST /api/v1/messages/conversations` — start or retrieve a 1-to-1 conversation by recipient username; returns 200
- `GET  /api/v1/messages/conversations` — list all conversations for the authenticated user; returns 200
- `GET  /api/v1/messages/{conversation_id}` — paginated message list (limit/offset); newest first; returns 200
- `POST /api/v1/messages/{conversation_id}` — send a text message; returns 201

#### Domain Exceptions
- `app/core/exceptions.py` — added `SelfMessageError` (→ 400), `ConversationNotFoundError` (→ 404), `MessagePermissionError` (→ 403)

#### Application Wiring
- `app/main.py` — exception handlers for `SelfMessageError`, `MessagePermissionError`, `ConversationNotFoundError`
- `app/api/v1/__init__.py` — `messages.router` registered at `/api/v1/messages/`
- `alembic/env.py` — `Conversation`, `ConversationParticipant`, `Message` imported for migration auto-detection

#### Migration
- `alembic/versions/d7a2e5f8b3c0_phase_9_add_direct_messaging_tables.py` — creates `message_type_enum`, `conversations`, `conversation_participants`, and `messages` tables with all columns, constraints, and indexes

#### Strictly excluded (per Phase 9 spec)
- ❌ WebSocket / live messaging
- ❌ Read receipts
- ❌ Typing indicators
- ❌ Media upload
- ❌ Group chat
- ❌ Notifications

---

## [0.6.0] — 2026-07-20

### Added — Phase 8: Privacy & Safety Foundation

#### Model
- `app/models/block.py` — `Block` ORM model; fields: `id` (UUID v4), `blocker_id` (FK → users.id CASCADE), `blocked_id` (FK → users.id CASCADE), `created_at`; UNIQUE constraint `uq_blocks_blocker_blocked`; CHECK constraint `ck_blocks_no_self_block`; indexes `ix_blocks_blocker_id`, `ix_blocks_blocked_id`, `ix_blocks_created_at`

#### Schemas
- `app/schemas/block.py` — `BlockRead`, `BlockedUserRead`, `BlockedListResponse`
- `app/schemas/user.py` — `UserPublicRead` extended with `is_blocked`, `has_blocked_me`

#### Repository
- `app/repositories/block_repo.py` — `BlockRepository`; methods: `get_block()`, `is_blocked()`, `is_mutually_blocked()`, `blocked_count()`, `blocked_users()`, `blocked_by_users()`, `block_user()`, `unblock_user()`

#### Service
- `app/services/block_service.py` — `BlockService`; methods: `block_user()`, `unblock_user()`, `get_blocked_users()`, `is_blocked_in_any_direction()`; business rules: no self-block, no inactive/deleted target, follow relationships auto-removed in both directions on block
- `app/services/privacy_guard.py` — `PrivacyGuard`; methods: `can_view_profile()`, `can_follow()`, `can_message()` (stub for Phase 11), `can_join_room()` (stub for Phase 9); all check for mutual block

#### API Endpoints
- `POST /api/v1/users/{username}/block` — block a user; removes follow in both directions (auth required); returns 201
- `DELETE /api/v1/users/{username}/block` — unblock a user (auth required); returns 204
- `GET /api/v1/users/blocked` — paginated list of blocked users (auth required); returns 200
- `GET /api/v1/users/{username}` — updated to include `is_blocked`, `has_blocked_me` when called with auth token

#### Domain Exceptions
- `app/core/exceptions.py` — added `SelfBlockError` (→ 400), `AlreadyBlockedError` (→ 409), `NotBlockedError` (→ 409)

#### Application Wiring
- `app/main.py` — exception handlers for `SelfBlockError`, `AlreadyBlockedError`, `NotBlockedError`
- `app/api/v1/__init__.py` — `blocks.router` registered before `users.router` (route precedence: static `/blocked` before dynamic `/{username}`)
- `alembic/env.py` — `Block` model imported for migration auto-detection

#### Migration
- `alembic/versions/c4f8e3b2d9a1_phase_8_add_blocks_table.py` — creates `blocks` table with all columns, constraints, and indexes

---

## [0.5.0] — 2026-07-20

### Added — Phase 7: Social Graph Foundation

#### Model
- `app/models/follow.py` — `Follow` ORM model; fields: `id` (UUID v4), `follower_id` (FK → users.id CASCADE), `following_id` (FK → users.id CASCADE), `created_at`; UNIQUE constraint `uq_follows_follower_following`; CHECK constraint `ck_follows_no_self_follow`; indexes `ix_follows_follower_id`, `ix_follows_following_id`, `ix_follows_created_at`

#### Schemas
- `app/schemas/follow.py` — `FollowRead`, `FollowUserRead`, `FollowListResponse`, `RelationshipRead`
- `app/schemas/user.py` — `UserPublicRead` extended with `followers_count`, `following_count`, `is_following`, `is_followed_by`

#### Repository
- `app/repositories/follow_repo.py` — `FollowRepository`; methods: `get_follow()`, `is_following()`, `followers_count()`, `following_count()`, `list_followers()`, `list_following()`, `followers_count_batch()`, `following_count_batch()`, `follow()`, `unfollow()`

#### Service
- `app/services/follow_service.py` — `FollowService`; methods: `follow_user()`, `unfollow_user()`, `get_followers()`, `get_following()`, `get_relationship()`, `get_social_counts()`; all business rules enforced (self-follow, inactive user, deleted user, duplicate follow, not-following)

#### API Endpoints
- `POST /api/v1/users/{username}/follow` — follow a user (auth required); returns 201
- `DELETE /api/v1/users/{username}/follow` — unfollow a user (auth required); returns 204
- `GET /api/v1/users/{username}/followers` — paginated followers list (public); returns 200
- `GET /api/v1/users/{username}/following` — paginated following list (public); returns 200
- `GET /api/v1/users/{username}/relationship` — mutual relationship status (auth required); returns 200
- `GET /api/v1/users/{username}` — updated to include `followers_count`, `following_count`; when called with auth token also includes `is_following`, `is_followed_by`

#### Domain Exceptions
- `app/core/exceptions.py` — added `SelfFollowError` (→ 400), `AlreadyFollowingError` (→ 409), `NotFollowingError` (→ 409)

#### Application Wiring
- `app/main.py` — exception handlers for `SelfFollowError`, `AlreadyFollowingError`, `NotFollowingError`
- `app/api/v1/__init__.py` — `follows.router` registered
- `app/services/auth/dependencies.py` — `get_optional_current_user` dependency added (optional Bearer token; returns `None` when header is absent)
- `alembic/env.py` — `Follow` model imported for migration auto-detection

#### Migration
- `alembic/versions/b3e9f2a1c5d8_phase_7_add_follows_table.py` — creates `follows` table with all columns, constraints, and indexes

---

## [0.4.0] — 2026-07-20

### Added — Phase 6: Extended User Profile Management

#### Domain Exceptions
- `app/core/exceptions.py` — added `UserNotFoundError` (404), `UsernameConflictError` (409), `ReservedUsernameError` (422)

#### User Model
- `app/models/user.py` — added `deleted_at` column (`TIMESTAMP WITH TIME ZONE`, nullable); NULL = active account, non-null = user-initiated soft-delete; reduced `username` column size from `VARCHAR(50)` to `VARCHAR(30)` to match validation rule; added `ix_users_deleted_at` index for efficient soft-delete filtering

#### Schemas
- `app/schemas/user.py` — added username regex validation (`^[a-z0-9_]{3,30}$`); added `RESERVED_USERNAMES` frozenset (80+ reserved names); added `@field_validator` for both `UserBase.username` and `UserUpdate.username`; added `UserPublicRead` (public profile — excludes firebase_uid, email, phone, birth_date); added `UserDeletedRead` (soft-delete confirmation response); updated `UserUpdate` to support `username` changes with validation

#### Repository
- `app/repositories/user_repo.py` — added `soft_delete()` (sets deleted_at + is_active=False, logs event); added `search_by_username_prefix()` (ILIKE prefix match, active-only, max 100 results, ordered by username)

#### Service
- `app/services/user_service.py` — added `get_by_username()` (active-only look-up with UserNotFoundError); added `update_my_profile()` (validates reserved names + uniqueness before delegating to repo); added `soft_delete_user()` (delegates to repo, logs event)

#### API Endpoints (Phase 6)
- `GET /api/v1/users/me` — protected; returns own full profile (`UserRead`)
- `PATCH /api/v1/users/me` — protected; partial profile update (`UserUpdate` → `UserRead`)
- `DELETE /api/v1/users/me` — protected; soft-delete own account (`UserDeletedRead`)
- `GET /api/v1/users/{username}` — public; returns public profile (`UserPublicRead`); 404 on missing/deleted

#### Application Wiring
- `app/api/v1/__init__.py` — registered `users.router` at `/api/v1/users/`
- `app/main.py` — added exception handlers: `UserNotFoundError` → 404, `UsernameConflictError` → 409, `ReservedUsernameError` → 422; reordered handlers most-specific-first

#### Migration
- `alembic/versions/a8f3d1c90e2b_phase_6_add_deleted_at_to_users.py` — adds `deleted_at` column, `ix_users_deleted_at` index, shrinks `username` to `VARCHAR(30)`

---

## [0.3.0] — 2026-07-20

### Added — Phase 5: Identity & Authentication Infrastructure

#### Exceptions
- `app/core/exceptions.py` — domain exception hierarchy: `VeeError` (root), `AuthError` (base auth), `AuthTokenInvalidError`, `AuthTokenExpiredError`, `AuthTokenRevokedError`, `FirebaseUnavailableError`, `InactiveUserError`; every exception carries a machine-readable `code` and human-readable `message`

#### Configuration
- `app/core/config.py` — added `FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, `FIREBASE_PRIVATE_KEY` fields; private key `\\n` normalization documented

#### Firebase Admin SDK
- `app/services/auth/firebase_init.py` — production-safe singleton; credentials from env vars (never from disk); `\\n` → newline normalization for PEM keys; private key never logged; `get_app()` reuse guard prevents double-initialization
- `app/services/auth/firebase.py` — `verify_firebase_token()` fully implemented; runs `verify_id_token` in thread-pool executor (non-blocking); maps `ExpiredIdTokenError`, `RevokedIdTokenError`, `InvalidIdTokenError`, `FirebaseError` → domain exceptions; only safe token prefix logged

#### Authentication Dependency
- `app/services/auth/dependencies.py` — `get_current_user()` fully implemented; uses `IdentityService.login_with_firebase()`; maps `InactiveUserError` → HTTP 403, `AuthError` → HTTP 401 with `WWW-Authenticate: Bearer`

#### Identity Service (new)
- `app/services/identity_service.py` — `IdentityService`; `login_with_firebase()` (verify → sync → guard inactive → update presence → return User); `get_identity()` (lightweight token introspection); designed for future provider extension

#### Repository
- `app/repositories/user_repo.py` — all methods implemented: `get_by_id`, `get_by_firebase_uid`, `get_by_username`, `get_by_email`, `create`, `update_last_seen`, `update_profile`, `save`

#### Service
- `app/services/user_service.py` — all methods implemented: `sync_firebase_user()`, `get_profile()`, `get_by_id()`, `update_last_seen()`

#### API Endpoints
- `POST /api/v1/auth/login` — verifies Firebase ID token (Bearer), syncs user, updates presence, returns `UserRead`
- `GET /api/v1/auth/me` — protected; returns current user profile via `get_current_user` dependency

#### Application Wiring
- `app/main.py` — global exception handlers for all auth errors
- `.env.example` — Firebase credential fields with setup instructions
- `requirements.txt` — `firebase-admin>=6.5.0`

---

## [0.2.0] — 2026-07-20

### Added — Phase 4: Core Domain Models & Authentication Foundation

#### Models
- `app/models/enums.py` — `Gender` string enum (`male`, `female`, `other`, `prefer_not_to_say`)
- `app/models/user.py` — `User` ORM model with 14 fields: `id` (UUID v4), `firebase_uid`, `username`, `display_name`, `email`, `phone`, `avatar_url`, `bio`, `gender`, `birth_date`, `is_verified`, `is_active`, `created_at`, `updated_at`, `last_seen_at`; composite index on `(is_active, created_at)`

#### Database Mixins
- `app/db/mixins.py` — `UUIDMixin` (UUID v4 primary key) and `TimestampMixin` (`created_at` / `updated_at` with `server_default=func.now()`)

#### Schemas
- `app/schemas/user.py` — `UserBase`, `UserRead`, `UserCreate`, `UserUpdate`; Pydantic v2 with `ConfigDict`
- `app/schemas/auth.py` — `FirebaseTokenPayload` (frozen), `AuthenticatedUser`

#### Repository
- `app/repositories/user_repo.py` — `UserRepository` skeleton

#### Service
- `app/services/user_service.py` — `UserService` skeleton

#### API & Routing
- `app/api/v1/__init__.py` — combined v1 router
- `app/api/v1/auth.py` — auth router structure
- `app/main.py` — v1 router mounted at `/api/v1`

#### Migration
- `alembic/versions/cfeccaac3dc7_phase_4_add_users_table.py` — creates `gender_enum` PostgreSQL type and `users` table with all columns and indexes

---

## [0.1.0] — 2026-07-20

### Added — Phase 1 & 2: Backend & Database Foundation

- FastAPI application with Uvicorn, Pydantic Settings, CORS
- `GET /` and `GET /health` endpoints
- Swagger UI (`/docs`) and ReDoc (`/redoc`)
- SQLAlchemy 2.x async engine (asyncpg), `DeclarativeBase`, `get_db` dependency
- `normalize_database_url()` utility
- Alembic configured for async migrations
- `requirements.txt`, `.env.example`, `.gitignore`, `README.md`
