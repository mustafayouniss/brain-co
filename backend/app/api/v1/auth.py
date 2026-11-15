"""
Auth endpoints: login, register-organization, switch-organization, and current-user.

Security design
---------------
- POST /auth/login returns uniform 401 (same status, body, header) for:
    unknown email, wrong password, inactive user.
  This prevents user-enumeration attacks (D-014).
- POST /auth/register-organization creates Organization, Admin User, and Membership atomically.
- POST /auth/switch-organization verifies organization membership in PostgreSQL.
- /auth/me delegates token validation to get_current_user and returns active tenant context.
- WWW-Authenticate: Bearer is sent on every 401 in this module.
"""
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.context import BrainContext, get_brain_context
from app.core.security import (
    TokenSecurityError,
    create_access_token,
    decode_access_token,
    hash_password,
    password_needs_rehash,
    verify_dummy_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    WSTicketRequest,
    WSTicketResponse,
)
from app.schemas.organization import (
    OrganizationMembershipResponse,
    OrganizationRegisterRequest,
    OrganizationResponse,
    OrganizationSignupResponse,
    SwitchOrganizationRequest,
)

router = APIRouter()
_bearer_scheme = HTTPBearer(auto_error=False)

_BEARER_HEADERS = {"WWW-Authenticate": "Bearer"}

_LOGIN_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid email or password",
    headers=_BEARER_HEADERS,
)


@router.post(
    "/register-organization",
    status_code=status.HTTP_201_CREATED,
    response_model=OrganizationSignupResponse,
)
def register_organization(
    body: OrganizationRegisterRequest,
    db: Session = Depends(get_db),
) -> OrganizationSignupResponse:
    """Register a new customer Organization with initial Administrator account and active domain."""
    from app.services.organization_service import OrganizationService
    from app.services.user_service import EmailAlreadyExistsError

    try:
        org, user, membership = OrganizationService.register_organization(
            session=db,
            company_name=body.company_name,
            admin_email=body.admin_email,
            admin_full_name=body.admin_full_name,
            password=body.password,
            domain=body.domain,
        )
        db.commit()
        db.refresh(org)
        db.refresh(user)
        db.refresh(membership)
    except EmailAlreadyExistsError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    token = create_access_token(
        subject=str(user.id),
        org_id=org.id,
        role=membership.role,
        domain=org.domain,
    )

    return OrganizationSignupResponse(
        organization=OrganizationResponse.model_validate(org),
        user=UserResponse.model_validate(user),
        membership=OrganizationMembershipResponse.model_validate(membership),
        access_token=token,
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate a user and return a Bearer access token scoped to active organization.

    Returns the same 401 for unknown email, wrong password, and inactive
    user — prevents user enumeration (D-014).
    """
    # body.email is already stripped and lowercased by LoginRequest validator
    user: User | None = db.query(User).filter(
        func.lower(User.email) == body.email
    ).first()

    if user is None:
        # Constant-time timing mitigation for unknown users
        verify_dummy_password(body.password)
        raise _LOGIN_401

    if not verify_password(body.password, user.hashed_password):
        raise _LOGIN_401

    if not user.is_active:
        raise _LOGIN_401

    # Opportunistic rehash: upgrade hash parameters silently on login
    if password_needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(body.password)
        db.add(user)
        db.commit()

    # Look up active organization memberships in PostgreSQL
    from app.services.organization_service import OrganizationService
    user_orgs = OrganizationService.list_user_organizations(db, user.id)

    selected_org = None
    selected_membership = None

    if body.organization_id:
        for org, mem in user_orgs:
            if org.id == body.organization_id:
                selected_org = org
                selected_membership = mem
                break
        if not selected_org:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not an authorized member of the requested organization",
                headers=_BEARER_HEADERS,
            )
    elif user_orgs:
        selected_org, selected_membership = user_orgs[0]
    else:
        # Fallback to default organization if present
        from app.models.organization import Organization, OrganizationMembership
        default_org = db.query(Organization).filter(Organization.id == "org-brain-corp").first()
        if default_org:
            selected_org = default_org
            selected_membership = OrganizationMembership(
                organization_id=default_org.id,
                user_id=user.id,
                role=user.role,
                is_active=True,
            )
            db.add(selected_membership)
            db.commit()

    org_id = selected_org.id if selected_org else "org-brain-corp"
    role = selected_membership.role if selected_membership else user.role
    domain = selected_org.domain if selected_org else "legal"

    token = create_access_token(
        subject=str(user.id),
        org_id=org_id,
        role=role,
        domain=domain,
    )
    return TokenResponse(
        access_token=token,
        organization_id=org_id,
        domain=domain,
    )


@router.post("/switch-organization", response_model=TokenResponse)
def switch_organization(
    body: SwitchOrganizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Switch active organization context for the authenticated user, strictly validating membership."""
    from app.services.organization_service import OrganizationService

    membership = OrganizationService.get_user_membership(
        session=db,
        user_id=current_user.id,
        organization_id=body.organization_id,
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not an authorized member of organization '{body.organization_id}'",
            headers=_BEARER_HEADERS,
        )

    org = OrganizationService.get_organization(db, body.organization_id)
    if not org or not org.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization '{body.organization_id}' not found or inactive",
        )

    token = create_access_token(
        subject=str(current_user.id),
        org_id=org.id,
        role=membership.role,
        domain=org.domain,
    )

    return TokenResponse(
        access_token=token,
        organization_id=org.id,
        domain=org.domain,
    )


@router.get("/me", response_model=UserResponse)
def me(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Return the authenticated user's profile, active organization context, and memberships."""
    from app.services.organization_service import OrganizationService

    token_org_id = None
    if credentials is not None:
        try:
            payload = decode_access_token(credentials.credentials)
            token_org_id = payload.get("org_id") or payload.get("organization_id")
        except Exception:
            pass

    user_orgs = OrganizationService.list_user_organizations(db, current_user.id)
    active_org = None
    if token_org_id:
        for o, m in user_orgs:
            if o.id == token_org_id:
                active_org = o
                break
    if not active_org and user_orgs:
        active_org = user_orgs[0][0]

    org_list = [
        {
            "id": o.id,
            "name": o.name,
            "slug": o.slug,
            "domain": o.domain,
            "role": m.role,
        }
        for o, m in user_orgs
    ]

    resp = UserResponse.model_validate(current_user)
    if active_org:
        resp.active_organization_id = active_org.id
        resp.active_organization_name = active_org.name
        resp.active_domain = active_org.domain
    resp.organizations = org_list
    return resp


@router.post(
    "/ws-ticket",
    response_model=WSTicketResponse,
    summary="Issue a short-lived single-use WebSocket ticket",
)
def create_websocket_ticket(
    body: WSTicketRequest = WSTicketRequest(),
    db: Session = Depends(get_db),
    context: BrainContext = Depends(get_brain_context),
) -> WSTicketResponse:
    """Issue a cryptographically secure, 60-second single-use ticket for WebSocket auth.

    Guarantees:
    1. Raw JWT is never exposed to client-side JavaScript.
    2. Ticket is bound to authenticated user_id, organization_id, and authorized case_id.
    3. Case access is strictly verified under CACS before ticket issuance.
    4. Plaintext ticket is NEVER logged or persisted to database.
    """
    from app.services.case_service import CaseNotFoundError, CaseService
    from app.services.ticket_service import TicketService

    if not context.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to request a WebSocket ticket",
            headers=_BEARER_HEADERS,
        )

    try:
        user_uuid = uuid.UUID(str(context.user_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in authentication context",
            headers=_BEARER_HEADERS,
        )

    user = db.get(User, user_uuid)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or not found",
            headers=_BEARER_HEADERS,
        )

    # Re-validate active membership in organization
    from app.services.organization_service import OrganizationService
    membership = OrganizationService.get_user_membership(db, user_uuid, context.organization_id)
    if not membership or not membership.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User is not an active member of organization '{context.organization_id}'",
            headers=_BEARER_HEADERS,
        )

    # If case_id requested, enforce CACS
    clean_case_id = None
    if body.case_id and body.case_id.strip():
        try:
            authorized_case = CaseService.validate_case_access(
                session=db,
                organization_id=context.organization_id,
                user_id=user_uuid,
                user_role=membership.role,
                case_id_or_number=body.case_id.strip(),
            )
            clean_case_id = str(authorized_case.id)
        except CaseNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case '{body.case_id}' not found or access denied",
            )

    raw_ticket = TicketService.create_ticket(
        session=db,
        user_id=user_uuid,
        organization_id=context.organization_id,
        case_id=clean_case_id,
    )
    db.commit()

    return WSTicketResponse(
        ticket=raw_ticket,
        expires_in=60,
    )

