from fastapi import APIRouter, Query, Request, Response, status, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.firebase_auth import get_current_user
from app.core.firebase_auth import initialize_firebase
from app.db.session import get_db
from app.core.limiter import limiter
from app.schemas.company_schema import (
    UploadUrlRequest,
    AdminCompanyProfileDetailsSchema,
)
from app.services.admin_panel_company_service import (
    get_all_approved_companies_service,
    get_all_draft_companies_service,
    get_all_unapproved_companies_service,
    get_company_details_by_id_service,
    admin_create_company_service,
    admin_update_company_service,
    update_company_status_to_approved_service,
    update_company_status_to_unapproved_service,
)
from app.services.company_service import generate_upload_url_service
from app.utils.response import custom_response
from uuid import UUID
from pydantic import BaseModel
from firebase_admin import auth

router = APIRouter()


# -----------------------Get All Approved Companies----------------------- #
@router.get(
    "/approved",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("10/minute")
def get_all_approved_companies(
    request: Request,  # REQUIRED by SlowAPI
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    cursor: str | None = Query(None),
    search_term: str | None = Query(None),
    search_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get approved and active companies with backend pagination.
    """
    company_details = get_all_approved_companies_service(
        db=db,
        page=page,
        page_size=page_size,
        cursor=cursor,
        search_term=search_term,
        search_type=search_type,
    )

    return custom_response(
        success=True,
        message="Approved company details and counts fetched successfully",
        data=company_details,
        code=status.HTTP_200_OK,
    )


# -----------------------End Get All Approved Companies----------------------- #


# -----------------------Get All Unapproved Companies----------------------- #
@router.get(
    "/unapproved",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("10/minute")
def get_all_unapproved_companies(
    request: Request,  # REQUIRED by SlowAPI
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    cursor: str | None = Query(None),
    search_term: str | None = Query(None),
    search_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get unapproved and active companies with backend pagination.
    """
    company_details = get_all_unapproved_companies_service(
        db=db,
        page=page,
        page_size=page_size,
        cursor=cursor,
        search_term=search_term,
        search_type=search_type,
    )

    return custom_response(
        success=True,
        message="Unapproved company details and counts fetched successfully",
        data=company_details,
        code=status.HTTP_200_OK,
    )


# -----------------------End Get All Unapproved Companies----------------------- #


# -----------------------Get All Draft Companies----------------------- #
@router.get(
    "/draft",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("10/minute")
def get_all_draft_companies(
    request: Request,  # REQUIRED by SlowAPI
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    cursor: str | None = Query(None),
    search_term: str | None = Query(None),
    search_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get draft and active companies with backend pagination.
    """
    company_details = get_all_draft_companies_service(
        db=db,
        page=page,
        page_size=page_size,
        cursor=cursor,
        search_term=search_term,
        search_type=search_type,
    )

    return custom_response(
        success=True,
        message="Draft company details and counts fetched successfully",
        data=company_details,
        code=status.HTTP_200_OK,
    )


# -----------------------End Get All Draft Companies----------------------- #


# -----------------------Get Company Details by ID----------------------- #
@router.get(
    "/{company_id}",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("10/minute")
def get_company_details_by_id(
    request: Request,
    company_id: str,
    db: Session = Depends(get_db),
):
    """
    Get company with full details (basic + addresses + bank details + documents)
    """
    company = get_company_details_by_id_service(db=db, company_id=company_id)

    return custom_response(
        success=True,
        message="Company details fetched successfully",
        data=company,
        code=status.HTTP_200_OK,
    )


# -----------------------End Get Company Details by ID----------------------- #


# -----------------------Update Company Status to Approved----------------------- #
@router.patch(
    "/approve_company_profile/{company_id}",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
def approve_company_profile(
    request: Request,  # REQUIRED by SlowAPI
    company_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Update company status to approved (Firebase authenticated) .
    """
    company_db = update_company_status_to_approved_service(
        company_id=company_id,
        db=db,
    )

    return custom_response(
        success=True,
        message="Company profile approved successfully",
        data={
            "id": company_db.id,
        },
        code=status.HTTP_200_OK,
    )


# -----------------------End Update Company Status to Approved----------------------- #


# -----------------------Update Company Status to Unapproved----------------------- #
@router.patch(
    "/unapprove/{company_id}",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
def unapprove_company(
    request: Request,  # REQUIRED by SlowAPI
    company_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Update company status to unapproved (Firebase authenticated) .
    """
    company_db = update_company_status_to_unapproved_service(
        company_id=company_id,
        db=db,
    )

    return custom_response(
        success=True,
        message="Company profile unapproved successfully",
        data={
            "id": company_db.id,
        },
        code=status.HTTP_200_OK,
    )


# -----------------------End Update Company Status to Unapproved----------------------- #


# -----------------------Generate S3 Upload URL----------------------- #
@router.put("/documents/upload-url")
@limiter.limit("30/minute")
def generate_upload_url(
    request: Request,  # REQUIRED by SlowAPI
    payload: UploadUrlRequest,
    firebase_uid: str,
):

    urls = generate_upload_url_service(
        file_type=payload.file_type, current_user=firebase_uid
    )

    return custom_response(
        success=True,
        message="Upload URL generated successfully",
        data=urls,
        code=status.HTTP_200_OK,
    )


# -----------------------End Generate S3 Upload URL----------------------- #


# -----------------------Create Company Firebase User----------------------- #
class CreateCompanyFirebaseUserRequest(BaseModel):
    phone_number: str


@router.post(
    "/create-company-firebase-user",
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
def create_company_firebase_user(
    request: Request,
    body: CreateCompanyFirebaseUserRequest,
    db: Session = Depends(get_db),
):
    """
    Create a Firebase user with phone number for company authentication.
    """
    try:
        initialize_firebase()
        user = auth.create_user(phone_number=body.phone_number)
        return custom_response(
            success=True,
            message="Firebase user created successfully",
            data={
                "firebase_uid": user.uid,
                "phone_number": user.phone_number,
            },
            code=status.HTTP_201_CREATED,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Firebase user: {str(e)}",
        )


# -----------------------End Create Company Firebase User----------------------- #


# -----------------------Create New Company----------------------- #
@router.post(
    "/create_new_company",
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
def create_new_company(
    request: Request,
    body: AdminCompanyProfileDetailsSchema,
    firebase_uid: str,
    db: Session = Depends(get_db),
):
    """
    Create a new company with details.
    """
    company_db = admin_create_company_service(
        db=db,
        company=body,
        firebase_uid=firebase_uid,
    )

    return custom_response(
        success=True,
        message="Company created successfully",
        data={},
        code=status.HTTP_201_CREATED,
    )


# -----------------------End Create New Company----------------------- #


# -----------------------Admin Update Company Details----------------------- #
@router.patch(
    "/{company_id}",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
def admin_update_company(
    request: Request,
    company_id: str,
    body: AdminCompanyProfileDetailsSchema,
    db: Session = Depends(get_db),
):
    """
    Admin can update company details.
    """
    company_db = admin_update_company_service(
        db=db,
        company_id=company_id,
        company=body,
    )

    return custom_response(
        success=True,
        message="Company details updated successfully",
        data={},
        code=status.HTTP_200_OK,
    )


# -----------------------End Admin Update Company Details----------------------- #
