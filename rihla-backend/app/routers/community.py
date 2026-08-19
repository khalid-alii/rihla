from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.exceptions import BadRequest
from app.models.community import Community
from app.models.user import User
from app.schemas.community import CommunityOut, CommunityVerifyOut, VerifyIn

router = APIRouter(prefix="/community", tags=["community"])


@router.post("/verify", response_model=CommunityVerifyOut)
def verify_community(
    body: VerifyIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommunityVerifyOut:
    # §6.2: strip + uppercase the input; compare against stored uppercase code.
    code = body.code.strip().upper()

    community = (
        db.query(Community)
        .filter(Community.code == code, Community.active.is_(True))
        .first()
    )

    # Same message for "code doesn't exist" and "active=false" — don't distinguish.
    if not community:
        raise BadRequest(
            "That code doesn't match a community. "
            "Check with your building or campus admin."
        )

    current_user.community_id = community.id
    db.commit()

    return CommunityVerifyOut(
        community=CommunityOut(id=str(community.id), name=community.name)
    )
