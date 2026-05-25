import os
import traceback
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from sqlalchemy.orm import Session, selectinload

from app.models.industry_skill_models import CategorySkillModel, SubCategorySkillModel
from app.models.worker_models import (
    WorkerBankDetailsModel,
    WorkerDocumentModel,
    WorkerRegistrationModel,
    WorkerSkillCategoryModel,
    WorkerSubCategoryModel,
)
from app.schemas.worker_schema import (
    CategorySelectionSchema,
    WorkerAddressUpdateSchema,
    WorkerBankDetailsSchema,
    WorkerDocumentCreateSchema,
    WorkerRegistrationSchema,
    WorkerSkillsUpdateSchema,
)
from app.utils.logger import logger

# Helper function for s3 upload url0.3]
import os
import boto3
from botocore.exceptions import ClientError


def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name="ap-south-2",
    )


def list_worker_docs():
    try:
        s3_client = get_s3_client()

        objects = s3_client.list_objects_v2(
            Bucket="workforce360-s3-bucket", Prefix="worker_docs/"
        )

        return objects

    except ClientError as e:
        print("S3 Error:", e)
        return None


# End helper function for s3 upload url

# -----------------------Get Worker Terms and Conditions Service----------------------- #
WORKER_TERMS_BUCKET_NAME = "workforce360-s3-bucket"
WORKER_TERMS_KEY = "worker_terms.html"


def get_worker_terms_and_conditions() -> str:
    try:
        s3_client = get_s3_client()
        response = s3_client.get_object(
            Bucket=WORKER_TERMS_BUCKET_NAME,
            Key=WORKER_TERMS_KEY,
        )

        html_content = response["Body"].read().decode("utf-8")
        return html_content

    except ClientError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to fetch Worker Terms and Conditions",
        )


# -----------------------End Get Worker Terms and Conditions Service----------------------- #

# ------------------------ Worker Registration Service ------------------------ #


def _build_location(latitude: Optional[float], longitude: Optional[float]):
    if latitude is None or longitude is None:
        return None
    return from_shape(Point(longitude, latitude), srid=4326)


def create_worker_service(
    worker: WorkerRegistrationSchema,
    db: Session,
    firebase_uid: str,
) -> dict:
    """
    Service function to create a new worker registration entry.
    """
    try:
        # Prevent duplicate registration
        existing = (
            db.query(WorkerRegistrationModel)
            .filter(WorkerRegistrationModel.firebase_uid == firebase_uid)
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Worker already registered",
            )

        reg = WorkerRegistrationModel(
            firebase_uid=firebase_uid,
            name=worker.name,
            country_code=worker.countryCode,
            auth_number=worker.authNumber,
            address=worker.address,
            city=worker.city,
            state=worker.state,
            pincode=worker.pincode,
            location=_build_location(worker.latitude, worker.longitude),
            logo_url=(worker.documentInfo.logoUrl if worker.documentInfo else None),
        )
        db.add(reg)
        db.flush()

        # ----------------------------
        # Handle Skills (Professional)
        # ----------------------------
        for category in worker.categories:

            # Insert category with experience
            worker_category = WorkerSkillCategoryModel(
                worker_id=reg.id,
                category_skill_id=category.categoryId,
                experience_years=category.experienceYears,
            )

            db.add(worker_category)
            # Validate subcategories belong to this category
            if category.subCategoryIds:

                valid_subs = (
                    db.query(SubCategorySkillModel.id)
                    .filter(
                        SubCategorySkillModel.id.in_(category.subCategoryIds),
                        SubCategorySkillModel.category_skill_id == category.categoryId,
                    )
                    .all()
                )

                valid_sub_ids = {str(v[0]) for v in valid_subs}

                for sub_id in category.subCategoryIds:
                    if sub_id not in valid_sub_ids:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid subcategory for selected category",
                        )

                    db.add(
                        WorkerSubCategoryModel(
                            worker_id=reg.id,
                            sub_category_skill_id=sub_id,
                        )
                    )
        # ----------------------------
        # Documents
        # ----------------------------
        if worker.documentInfo and worker.documentInfo.documents:
            for doc in worker.documentInfo.documents:
                db.add(
                    WorkerDocumentModel(
                        worker_id=reg.id,
                        document_type=doc.documentType,
                        document_url=doc.documentUrl,
                    )
                )
        db.flush()
        return {"id": str(reg.id), "name": reg.name}

    except HTTPException:
        raise
    except Exception as e:
        print("create_worker_service DB ERROR:", str(e))
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating worker registration",
        )


# -----------------------END Worker Registration Service -----------------------


# -----------------------Worker profile exist or not Service ----------------------- #
def worker_profile_exist_service(
    firebase_uid: str,
    db: Session,
) -> WorkerRegistrationModel | None:
    return (
        db.query(WorkerRegistrationModel)
        .filter(WorkerRegistrationModel.firebase_uid == firebase_uid)
        .first()
    )


# -----------------------End Worker profile exist or not Service ----------------------- #


# -----------------------Get Worker Profile Service ----------------------- #
def get_worker_profile_service(
    firebase_uid: str,
    db: Session,
) -> dict:
    try:
        worker = (
            db.query(WorkerRegistrationModel)
            .options(
                selectinload(WorkerRegistrationModel.categories),
                selectinload(WorkerRegistrationModel.sub_categories),
                selectinload(WorkerRegistrationModel.documents),
                selectinload(WorkerRegistrationModel.bank_details),
            )
            .filter(WorkerRegistrationModel.firebase_uid == firebase_uid)
            .first()
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        point = to_shape(worker.location) if worker.location else None

        category_ids = [c.category_skill_id for c in worker.categories]
        sub_category_ids = [s.sub_category_skill_id for s in worker.sub_categories]

        category_rows = (
            db.query(CategorySkillModel.id, CategorySkillModel.name)
            .filter(CategorySkillModel.id.in_(category_ids))
            .all()
            if category_ids
            else []
        )
        sub_category_rows = (
            db.query(
                SubCategorySkillModel.id,
                SubCategorySkillModel.name,
                SubCategorySkillModel.category_skill_id,
            )
            .filter(SubCategorySkillModel.id.in_(sub_category_ids))
            .all()
            if sub_category_ids
            else []
        )

        category_name_map = {row.id: row.name for row in category_rows}
        sub_category_map = {
            row.id: {"name": row.name, "category_skill_id": row.category_skill_id}
            for row in sub_category_rows
        }

        categories = []
        for category in worker.categories:
            matched_sub_ids = []
            matched_sub_names = []
            for sub in worker.sub_categories:
                sub_data = sub_category_map.get(sub.sub_category_skill_id)
                if not sub_data:
                    continue
                if sub_data["category_skill_id"] == category.category_skill_id:
                    matched_sub_ids.append(str(sub.sub_category_skill_id))
                    matched_sub_names.append(sub_data["name"])

            categories.append(
                {
                    "categoryId": str(category.category_skill_id),
                    "categoryName": category_name_map.get(category.category_skill_id),
                    "experienceYears": category.experience_years,
                    "subCategoryIds": matched_sub_ids,
                    "subCategoryNames": matched_sub_names,
                }
            )

        return {
            "id": str(worker.id),
            "firebase_uid": worker.firebase_uid,
            "name": worker.name,
            "countryCode": worker.country_code,
            "authNumber": worker.auth_number,
            "logoUrl": worker.logo_url,
            "categories": categories,
            "address": worker.address,
            "city": worker.city,
            "state": worker.state,
            "pincode": worker.pincode,
            "latitude": point.y if point else None,
            "longitude": point.x if point else None,
            "documents": [
                {
                    "documentType": d.document_type,
                    "documentUrl": d.document_url,
                }
                for d in worker.documents
            ],
            "bank_details": [
                {
                    "bank_name": bank.bank_name,
                    "account_holder_name": bank.account_holder_name,
                    "account_number": bank.account_number,
                    "ifsc_code": bank.ifsc_code,
                    "upi_id": bank.upi_id,
                }
                for bank in worker.bank_details
            ],
            "status": worker.status,
            "is_active": worker.is_active,
            "is_online": worker.is_online,
            "is_available": worker.is_available,
            "currentJobId": (
                str(worker.current_job_id) if worker.current_job_id else None
            ),
            "created_at": worker.created_at,
            "updated_at": worker.updated_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        print("get_worker_profile_service DB ERROR:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching worker profile",
        )


# -----------------------End Get Worker Profile Service ----------------------- #


# -----------------------Get All Worker Details Service----------------------- #
def get_all_worker_details_service(
    db: Session,
) -> list[dict]:
    try:
        workers = (
            db.query(WorkerRegistrationModel)
            .options(
                selectinload(WorkerRegistrationModel.categories),
                selectinload(WorkerRegistrationModel.sub_categories),
                selectinload(WorkerRegistrationModel.bank_details),
            )
            .all()
        )

        category_ids = {
            category.category_skill_id
            for worker in workers
            for category in worker.categories
        }
        sub_category_ids = {
            sub.sub_category_skill_id
            for worker in workers
            for sub in worker.sub_categories
        }

        category_rows = (
            db.query(CategorySkillModel.id, CategorySkillModel.name)
            .filter(CategorySkillModel.id.in_(category_ids))
            .all()
            if category_ids
            else []
        )
        sub_category_rows = (
            db.query(
                SubCategorySkillModel.id,
                SubCategorySkillModel.name,
                SubCategorySkillModel.category_skill_id,
            )
            .filter(SubCategorySkillModel.id.in_(sub_category_ids))
            .all()
            if sub_category_ids
            else []
        )

        category_name_map = {row.id: row.name for row in category_rows}
        sub_category_map = {
            row.id: {"name": row.name, "category_skill_id": row.category_skill_id}
            for row in sub_category_rows
        }

        worker_details = []
        for worker in workers:
            # point = to_shape(worker.location) if worker.location else None
            categories = []
            category_ids_for_worker = []
            category_names_for_worker = []
            years_for_worker = []

            for category in worker.categories:
                matched_sub_ids = []
                matched_sub_names = []
                for sub in worker.sub_categories:
                    sub_data = sub_category_map.get(sub.sub_category_skill_id)
                    if not sub_data:
                        continue
                    if sub_data["category_skill_id"] == category.category_skill_id:
                        matched_sub_ids.append(str(sub.sub_category_skill_id))
                        matched_sub_names.append(sub_data["name"])

                categories.append(
                    {
                        "categoryId": str(category.category_skill_id),
                        "categoryName": category_name_map.get(
                            category.category_skill_id
                        ),
                        "experienceYears": category.experience_years,
                        "subCategoryIds": matched_sub_ids,
                        "subCategoryNames": matched_sub_names,
                    }
                )

                category_ids_for_worker.append(str(category.category_skill_id))
                category_names_for_worker.append(
                    category_name_map.get(category.category_skill_id)
                )
                years_for_worker.append(category.experience_years)

            worker_details.append(
                {
                    "id": str(worker.id),
                    "firebase_uid": worker.firebase_uid,
                    "name": worker.name,
                    "country_code": worker.country_code,
                    "authNumber": worker.auth_number,
                    "categoryId": category_ids_for_worker,
                    "categoryName": category_names_for_worker,
                    "address": worker.address,
                    "city": worker.city,
                    "state": worker.state,
                    "pincode": worker.pincode,
                    "years": years_for_worker,
                    "categories": categories,
                    "logoUrl": worker.logo_url,
                    "status": worker.status,
                    "statusApprovalMessageShown": worker.status_approval_message_shown,
                    "is_active": worker.is_active,
                    "created_at": worker.created_at,
                    "updated_at": worker.updated_at,
                }
            )

        return worker_details
    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR =>", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching all worker details",
        )


# -----------------------End Get All Worker Details Service----------------------- #


# -----------------------Delete Worker Details Service----------------------- #
def delete_worker_profile_service(
    auth_number: str,
    db: Session,
) -> WorkerRegistrationModel:
    try:
        worker = (
            db.query(WorkerRegistrationModel)
            .filter(WorkerRegistrationModel.auth_number == auth_number)
            .first()
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        db.query(WorkerSubCategoryModel).filter(
            WorkerSubCategoryModel.worker_id == worker.id
        ).delete()

        db.query(WorkerDocumentModel).filter(
            WorkerDocumentModel.worker_id == worker.id
        ).delete()

        db.query(WorkerBankDetailsModel).filter(
            WorkerBankDetailsModel.worker_id == worker.id
        ).delete()

        db.delete(worker)
        db.flush()

        return worker

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR =>", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting worker details",
        )


# -----------------------End Delete Worker Details Service----------------------- #


# -----------------------Get Worker Documents by Type Service----------------------- #
def get_worker_documents_by_type_service(
    firebase_uid: str,
    document_type: str,
    db: Session,
) -> list[WorkerDocumentModel]:
    try:
        worker = (
            db.query(WorkerRegistrationModel)
            .filter(WorkerRegistrationModel.firebase_uid == firebase_uid)
            .first()
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        documents = (
            db.query(WorkerDocumentModel)
            .filter(
                WorkerDocumentModel.worker_id == worker.id,
                WorkerDocumentModel.document_type == document_type,
            )
            .all()
        )

        return documents

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR =>", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching worker documents by type",
        )


# -----------------------End Get Worker Documents by Type Service----------------------- #


# -----------------------Update Worker Logo Service----------------------- #
def update_worker_logo_service(
    logo_url: str,
    firebase_uid: str,
    db: Session,
) -> WorkerRegistrationModel:
    try:
        worker = (
            db.query(WorkerRegistrationModel)
            .filter(WorkerRegistrationModel.firebase_uid == firebase_uid)
            .first()
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        worker.logo_url = logo_url
        db.flush()
        return worker

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR =>", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating worker logo",
        )


# -----------------------End Update Worker Logo Service----------------------- #


# -----------------------Add more documents against worker id & document type service----------------------- #
def add_document_against_worker_id_and_type_service(
    firebase_uid: str,
    db: Session,
    document_info: WorkerDocumentCreateSchema,
):
    try:
        worker = (
            db.query(WorkerRegistrationModel)
            .filter(WorkerRegistrationModel.firebase_uid == firebase_uid)
            .first()
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        document = WorkerDocumentModel(
            document_type=document_info.documentType,
            document_url=document_info.documentUrl,
            worker_id=worker.id,
        )
        db.add(document)
        worker.status = "unapproved"
        worker.status_approval_message_shown = False
        db.flush()
        return document

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR =>", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding document against worker id and type",
        )


# -----------------------End Add more documents against worker id & document type service----------------------- #


# -----------------------Get worker name and status Service----------------------- #
def worker_name_and_status_service(
    firebase_uid: str,
    db: Session,
) -> dict:
    try:
        worker = (
            db.query(WorkerRegistrationModel)
            .filter(WorkerRegistrationModel.firebase_uid == firebase_uid)
            .first()
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        show_approval_message = False
        if worker.status == "approved" and not worker.status_approval_message_shown:
            show_approval_message = True
            worker.status_approval_message_shown = True
            db.flush()

        return {
            "name": worker.name,
            "logoUrl": worker.logo_url,
            "status": worker.status,
            # "statusApprovalMessageShown": worker.status_approval_message_shown,
            "showApprovalMessage": show_approval_message,
            "workerId": str(worker.id),
            "fcmToken": worker.fcm_token,
        }

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR =>", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching worker name and status",
        )


# -----------------------End Get worker name and status Service----------------------- #


# -----------------------Update Worker Address Service ----------------------- #
def update_worker_address_service(
    firebase_uid: str,
    address: WorkerAddressUpdateSchema,
    db: Session,
) -> WorkerRegistrationModel:
    try:
        worker = (
            db.query(WorkerRegistrationModel)
            .filter(WorkerRegistrationModel.firebase_uid == firebase_uid)
            .first()
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        if address.address is not None:
            worker.address = address.address
        if address.city is not None:
            worker.city = address.city
        if address.state is not None:
            worker.state = address.state
        if address.pincode is not None:
            worker.pincode = address.pincode

        if address.latitude is not None and address.longitude is not None:
            worker.location = _build_location(address.latitude, address.longitude)

        db.flush()
        return worker

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR =>", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating worker address",
        )


# -----------------------End Update Worker Address Service ----------------------- #


# -----------------------Update Worker Skills Service ----------------------- #
def update_worker_skills_service(
    firebase_uid: str,
    skills: WorkerSkillsUpdateSchema,
    db: Session,
) -> WorkerRegistrationModel:
    try:
        worker = (
            db.query(WorkerRegistrationModel)
            .filter(WorkerRegistrationModel.firebase_uid == firebase_uid)
            .first()
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        category_ids = [category.categoryId for category in skills.categories]
        if len(category_ids) != len(set(category_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate category ids are not allowed",
            )

        if category_ids:
            valid_categories = (
                db.query(CategorySkillModel.id)
                .filter(CategorySkillModel.id.in_(category_ids))
                .all()
            )
            valid_category_ids = {str(row[0]) for row in valid_categories}
            for category_id in category_ids:
                if category_id not in valid_category_ids:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid category id provided",
                    )

        db.query(WorkerSubCategoryModel).filter(
            WorkerSubCategoryModel.worker_id == worker.id
        ).delete()
        db.query(WorkerSkillCategoryModel).filter(
            WorkerSkillCategoryModel.worker_id == worker.id
        ).delete()

        for category in skills.categories:
            db.add(
                WorkerSkillCategoryModel(
                    worker_id=worker.id,
                    category_skill_id=category.categoryId,
                    experience_years=category.experienceYears,
                )
            )

            if not category.subCategoryIds:
                continue

            if len(category.subCategoryIds) != len(set(category.subCategoryIds)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Duplicate subcategory ids are not allowed",
                )

            valid_sub_categories = (
                db.query(SubCategorySkillModel.id)
                .filter(
                    SubCategorySkillModel.id.in_(category.subCategoryIds),
                    SubCategorySkillModel.category_skill_id == category.categoryId,
                )
                .all()
            )
            valid_sub_ids = {str(row[0]) for row in valid_sub_categories}

            for sub_category_id in category.subCategoryIds:
                if sub_category_id not in valid_sub_ids:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid subcategory for selected category",
                    )

                db.add(
                    WorkerSubCategoryModel(
                        worker_id=worker.id,
                        sub_category_skill_id=sub_category_id,
                    )
                )

        db.flush()
        return worker

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR =>", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating worker skills",
        )


# -----------------------End Update Worker Skills Service ----------------------- #


# -----------------------Add Worker Skill Category Service----------------------- #
def add_worker_skill_category_service(
    firebase_uid: str,
    category: CategorySelectionSchema,
    db: Session,
) -> dict:
    try:
        worker = (
            db.query(WorkerRegistrationModel)
            .filter(WorkerRegistrationModel.firebase_uid == firebase_uid)
            .first()
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        valid_category = (
            db.query(CategorySkillModel.id)
            .filter(CategorySkillModel.id == category.categoryId)
            .first()
        )
        if not valid_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category id provided",
            )

        existing_worker_category = (
            db.query(WorkerSkillCategoryModel)
            .filter(
                WorkerSkillCategoryModel.worker_id == worker.id,
                WorkerSkillCategoryModel.category_skill_id == category.categoryId,
            )
            .first()
        )
        if existing_worker_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category already exists for worker",
            )

        if len(category.subCategoryIds) != len(set(category.subCategoryIds)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate subcategory ids are not allowed",
            )

        db.add(
            WorkerSkillCategoryModel(
                worker_id=worker.id,
                category_skill_id=category.categoryId,
                experience_years=category.experienceYears,
            )
        )

        if category.subCategoryIds:
            valid_sub_categories = (
                db.query(SubCategorySkillModel.id)
                .filter(
                    SubCategorySkillModel.id.in_(category.subCategoryIds),
                    SubCategorySkillModel.category_skill_id == category.categoryId,
                )
                .all()
            )
            valid_sub_ids = {str(row[0]) for row in valid_sub_categories}

            for sub_category_id in category.subCategoryIds:
                if sub_category_id not in valid_sub_ids:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid subcategory for selected category",
                    )
                db.add(
                    WorkerSubCategoryModel(
                        worker_id=worker.id,
                        sub_category_skill_id=sub_category_id,
                    )
                )

        db.flush()
        return {
            "worker_id": str(worker.id),
            "category_id": str(category.categoryId),
        }

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR =>", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding worker skill category",
        )


# -----------------------End Add Worker Skill Category Service----------------------- #


# -----------------------Delete Worker Skill Category Service----------------------- #
def delete_worker_skill_category_service(
    firebase_uid: str,
    category_id: str,
    db: Session,
) -> dict:
    try:
        worker = (
            db.query(WorkerRegistrationModel)
            .filter(WorkerRegistrationModel.firebase_uid == firebase_uid)
            .first()
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        worker_category = (
            db.query(WorkerSkillCategoryModel)
            .filter(
                WorkerSkillCategoryModel.worker_id == worker.id,
                WorkerSkillCategoryModel.category_skill_id == category_id,
            )
            .first()
        )

        if not worker_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker category not found",
            )

        sub_category_ids = (
            db.query(SubCategorySkillModel.id)
            .filter(SubCategorySkillModel.category_skill_id == category_id)
            .all()
        )
        sub_category_ids = [row[0] for row in sub_category_ids]

        deleted_sub_categories = 0
        if sub_category_ids:
            deleted_sub_categories = (
                db.query(WorkerSubCategoryModel)
                .filter(
                    WorkerSubCategoryModel.worker_id == worker.id,
                    WorkerSubCategoryModel.sub_category_skill_id.in_(sub_category_ids),
                )
                .delete(synchronize_session=False)
            )

        db.delete(worker_category)
        db.flush()

        return {
            "worker_id": str(worker.id),
            "category_id": str(category_id),
            "deleted_sub_categories": deleted_sub_categories,
        }

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR =>", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting worker category",
        )


# -----------------------End Delete Worker Skill Category Service----------------------- #


# -----------------------Create Worker Bank Details Service----------------------- #
def create_worker_bank_details_service(
    firebase_uid: str,
    bank_details: WorkerBankDetailsSchema,
    db: Session,
) -> WorkerRegistrationModel:
    try:
        worker = (
            db.query(WorkerRegistrationModel)
            .filter(WorkerRegistrationModel.firebase_uid == firebase_uid)
            .first()
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        new_worker_bank = WorkerBankDetailsModel(
            worker_id=worker.id,
            bank_name=bank_details.bankName,
            account_holder_name=bank_details.accountHolderName,
            account_number=bank_details.accountNumber,
            ifsc_code=bank_details.ifscCode,
            upi_id=bank_details.upiId,
        )
        db.add(new_worker_bank)
        db.flush()

        return worker

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR =>", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating worker bank details",
        )


# -----------------------End Create Worker Bank Details Service----------------------- #


# -----------------------Update Worker Bank Details Service----------------------- #
def update_worker_bank_details_service(
    firebase_uid: str,
    bank_details: WorkerBankDetailsSchema,
    db: Session,
) -> WorkerRegistrationModel:
    try:
        worker = (
            db.query(WorkerRegistrationModel)
            .filter(WorkerRegistrationModel.firebase_uid == firebase_uid)
            .first()
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        worker_bank = (
            db.query(WorkerBankDetailsModel)
            .filter(WorkerBankDetailsModel.worker_id == worker.id)
            .first()
        )

        if not worker_bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker bank details not found",
            )

        worker_bank.bank_name = bank_details.bankName
        worker_bank.account_holder_name = bank_details.accountHolderName
        worker_bank.account_number = bank_details.accountNumber
        worker_bank.ifsc_code = bank_details.ifscCode
        worker_bank.upi_id = bank_details.upiId

        # If bank details are updated, we can consider worker profile as unapproved and require admin approval again
        worker.status = "unapproved"
        worker.status_approval_message_shown = False
        db.flush()
        return worker

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR =>", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating worker bank details",
        )


# -----------------------End Update Worker Bank Details Service----------------------- #


# # -----------------------Generate S3 Upload URL Service----------------------- #
def generate_upload_url_service(
    file_type: str,
    current_user,
) -> dict:
    try:
        allowed_types = ["png", "jpg", "jpeg", "pdf"]
        if file_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type",
            )

        CONTENT_TYPES = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "pdf": "application/pdf",
        }

        key = f"worker_docs/{current_user}/{uuid4()}.{file_type}"

        s3_client = get_s3_client()
        url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": "workforce360-s3-bucket",
                "Key": key,
                "ContentType": CONTENT_TYPES[file_type],
            },
            ExpiresIn=300,  # 5 minutes
        )

        return {
            "upload_url": url,
            "file_url": f"https://workforce360-s3-bucket.s3.amazonaws.com/{key}",
        }

    except HTTPException:
        raise
    except Exception as e:
        print("S3 ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating upload URL",
        )


# -----------------------End Generate S3 Upload URL Service----------------------- #


# -----------------------Update Worker Status to Approved Service----------------------- #
def update_worker_status_to_approved_service(worker_id: UUID, db: Session):
    try:
        worker = (
            db.query(WorkerRegistrationModel)
            .filter(WorkerRegistrationModel.id == worker_id)
            .first()
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        was_approved = worker.status == "approved"
        worker.status = "approved"
        if not was_approved:
            worker.status_approval_message_shown = False
        db.flush()
        return worker

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR =>", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating worker status to approved",
        )


# -----------------------End Update Worker Status to Approved Service----------------------- #


def update_worker_fcm_token_service(
    worker_id: UUID,
    fcm_token: str,
    db: Session,
) -> WorkerRegistrationModel:
    """
    Update worker FCM token (single-device support).
    """
    try:
        worker = (
            db.query(WorkerRegistrationModel)
            .filter(WorkerRegistrationModel.id == worker_id)
            .first()
        )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker profile not found",
            )

        normalized_token = fcm_token.strip()
        if not normalized_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="fcm_token cannot be empty",
            )

        worker.fcm_token = normalized_token
        db.flush()
        logger.info("FCM token updated for worker_id=%s", worker_id)
        return worker

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to update FCM token for worker_id=%s", worker_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating worker FCM token",
        )
